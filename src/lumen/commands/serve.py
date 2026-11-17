"""Launch one persistent RTL process from this checkout, using a fresh run folder."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
from lumen.commands.preflight import check, ROOT


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--arm', choices=('base', 'evidence'), required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--bind', default='tcp://127.0.0.1:5671')
    p.add_argument('--build', type=Path, default=ROOT / '.build/wb_pmp')
    p.add_argument('--smoke-rounds', type=int, default=0)
    p.add_argument('--platform-validation', action='store_true')
    p.add_argument('--seed', type=Path)
    p.add_argument('--provider-config', type=Path, help='Provider metadata only; cannot override scoring or RTL parameters')
    args = p.parse_args()
    if args.smoke_rounds < 0 or (args.platform_validation and args.smoke_rounds):
        p.error('Use a positive smoke limit or platform validation, not both.')
    if args.seed and (args.arm != 'evidence' or args.smoke_rounds or args.platform_validation):
        p.error('A completed baseline seed is only allowed for a full evidence experiment.')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    claim = output / 'run_claim.json'
    if any(output.iterdir()):
        p.error('Output must be a new empty directory; existing runs are never overwritten.')
    check()
    with claim.open('x') as stream:
        json.dump(dict(pid=os.getpid(), created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()), stream)
    config = json.loads((ROOT / 'profiles/experiment.json').read_text())
    config.update(run_kind='platform_validation' if args.platform_validation else 'smoke' if args.smoke_rounds else 'experiment',
                  smoke_max_responses=args.smoke_rounds, formal_llm_enabled=not args.platform_validation)
    if args.provider_config:
        metadata = json.loads(args.provider_config.read_text())
        allowed = {'model', 'model_context_policy', 'execution_mode', 'llm_api_used', 'formal_llm_enabled'}
        if set(metadata) != allowed or metadata['model'].get('provider') not in ('openai_compatible', 'local_http_fixture'):
            p.error('Invalid provider metadata; scoring and timing overrides are not permitted')
        fixture = metadata['model']['provider'] == 'local_http_fixture'
        if fixture != (not metadata['formal_llm_enabled']) or metadata['llm_api_used'] == fixture:
            p.error('Provider identity and experiment flags disagree')
        if args.platform_validation or (fixture and not args.smoke_rounds):
            p.error('API metadata requires an API run; local fixtures require smoke rounds')
        config.update(metadata)
    if args.seed:
        seed = json.loads(args.seed.read_text())
        if seed.get('baseline_model') != config['model']:
            p.error('Evidence must use the same provider/model/settings as its baseline seed')
    (output / 'effective_config.json').write_text(json.dumps(config, indent=2))
    profiles = json.loads((ROOT / 'profiles/ibex.json').read_text())
    profile = profiles['wb_pmp']
    (output / 'profile.json').write_text(json.dumps(dict(profile='wb_pmp', parameters=profile), indent=2))
    (output / 'run_provenance.json').write_text(json.dumps(dict(
        python=sys.version, verilator=subprocess.check_output(['verilator', '--version'], text=True).strip(),
        source_root=str(ROOT), source_manifest_sha256=hashlib.sha256((ROOT / 'SOURCE_MANIFEST.json').read_bytes()).hexdigest(),
        profile=profile, catalog_sha256=config['catalog_sha256'], run_kind=config['run_kind']), indent=2))
    env = dict(os.environ, LUMEN_ROOT=str(ROOT), LUMEN_PROFILE='wb_pmp', LUMEN_CATALOG='official_current',
               LUMEN_ARM=args.arm, LUMEN_BIND=args.bind, LUMEN_OUTPUT=str(output),
               LUMEN_EXPERIMENT_CONFIG=str(output / 'effective_config.json'), PYTHONDONTWRITEBYTECODE='1',
               PYTHONPATH=str(ROOT / 'src') + os.pathsep + str(ROOT / 'targets/ibex/bench'))
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    env.pop('LUMEN_COVERAGE_SEED', None)
    if args.seed:
        env['LUMEN_COVERAGE_SEED'] = str(args.seed.resolve())
    bench = ROOT / 'targets/ibex/bench'
    # GNU Make's inherited PWD can refer to the caller instead of the bench.
    env['PWD'] = str(bench)
    cmd = ['make', '-j2', 'MODULE=cocotb_session', 'IBEX_WRAPPER=lumen_top.sv', 'LUMEN_RTL_FCOV=1',
           'LUMEN_PARAM_ARGS=' + ' '.join('-G%s=%s' % item for item in profile.items()),
           'PLUSARGS=+ibex_tracer_enable=0', 'SIM_BUILD=' + str(args.build.resolve()),
           'COCOTB_RESULTS_FILE=' + str(output / 'results.xml'), 'sim']
    with (output / 'simulation.log').open('w') as log:
        result = subprocess.run(cmd, cwd=bench, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise SystemExit('RTL failed; inspect ' + str(output / 'simulation.log'))
    tree = ET.parse(output / 'results.xml')
    if not tree.findall('.//testcase') or tree.findall('.//failure') or tree.findall('.//error'):
        raise SystemExit('cocotb reported failure; inspect ' + str(output / 'simulation.log'))
    print('Lumen simulation PASS', flush=True)


if __name__ == '__main__':
    main()
