"""Optional real-Ibex backend with input replay and arrival checks before suffixes."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET
from lumen.paths import ROOT, IBEX, PROFILES, catalog_path
from lumen.engine.actions import validate
from lumen.engine import artifacts
from lumen.engine.interfaces import Environment, Execution


class IbexBatchBackend:
    def __init__(self, output, build=None):
        self.output = Path(output).resolve()
        self.output.mkdir(parents=True, exist_ok=True)
        self.build = Path(build or ROOT / '.build/paper_ibex').resolve()
        self.profile = json.loads((PROFILES / 'ibex.json').read_text())['wb_pmp']
        # Runtime semantics are part of compatibility, not just the RTL revision.
        inputs = sorted(p for base in (IBEX / 'rtl', IBEX / 'bench', ROOT / 'src/lumen/coverage', ROOT / 'src/lumen/observation')
                        for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.sv', '.svh', '.py'))
        digest = hashlib.sha256()
        for path in inputs:
            digest.update(path.relative_to(ROOT).as_posix().encode())
            digest.update(path.read_bytes())
        self.environment = Environment(digest.hexdigest(), hashlib.sha256(catalog_path().read_bytes()).hexdigest(),
            self.profile, dict(cpu='fresh_process', reset_cycles=4, memories='empty'),
            dict(default_word='0xc0001073', grant=1, instruction_latency=2, data_latency=2), None)
        self.catalog_ids = {r['id'] for r in json.loads(catalog_path().read_text())['targets']}

    def execute(self, actions, *, prefix=None, observers=()):
        # This backend exposes existing trace columns. Arbitrary new RTL probes require a different adapter.
        for observer in observers:
            if (observer.get('phase') != 'pre_edge_effective'
                    or observer.get('hierarchy') != 'trace.' + observer.get('node', '')
                    or type(observer.get('width')) is not int or observer['width'] <= 0
                    or type(observer.get('lsb', 0)) is not int or observer.get('lsb', 0) < 0):
                return Execution(False, [], [], set(), 0, self.environment, False, error='unsupported_observer_binding')
        prefix_actions = prefix['actions'] if prefix else []
        if prefix and prefix['environment_sha256'] != self.environment.fingerprint:
            return Execution(False, [], [], set(), 0, self.environment, False, error='prefix_environment_mismatch')
        complete = prefix_actions + actions
        if not complete:
            return Execution(False, [], [], set(), 0, self.environment, False, error='empty_plan')
        try:
            for action in complete:
                checked = validate(action)
                if checked['target'] is not None and checked['target'] not in self.catalog_ids:
                    raise ValueError('Unknown frozen target')
            if prefix and (not prefix['arrival'] or any(c['offset'] != 0 or c['op'] not in ('eq', 'ne') for c in prefix['arrival'])):
                raise ValueError('Invalid prefix arrival contract')
        except (ValueError, TypeError, KeyError) as exc:
            return Execution(False, [], [], set(), 0, self.environment, False, error='invalid_plan: ' + str(exc))
        folder = self.output / ('execution_' + uuid.uuid4().hex)
        folder.mkdir()
        plan = dict(actions=complete, prefix_length=len(prefix_actions), arrival=prefix['arrival'] if prefix else [], observers=observers)
        (folder / 'plan.json').write_text(json.dumps(plan, indent=2))
        bench = IBEX / 'bench'
        env = dict(os.environ, LUMEN_PROFILE='wb_pmp', LUMEN_CATALOG='official_current',
                   LUMEN_OUTPUT=str(folder), LUMEN_PLAN=str(folder / 'plan.json'), PWD=str(bench),
                   PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT / 'src') + os.pathsep + str(bench))
        # Always use this Python environment's cocotb tools.
        env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
        cmd = ['make', '-j2', 'MODULE=cocotb_plan', 'IBEX_WRAPPER=lumen_top.sv', 'LUMEN_RTL_FCOV=1',
               'LUMEN_PARAM_ARGS=' + ' '.join('-G%s=%s' % item for item in self.profile.items()),
               'PLUSARGS=+ibex_tracer_enable=0', 'SIM_BUILD=' + str(self.build),
               'COCOTB_RESULTS_FILE=' + str(folder / 'results.xml'), 'sim']
        with (folder / 'simulation.log').open('w') as log:
            result = subprocess.run(cmd, cwd=bench, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=300)
        if result.returncode or not (folder / 'plan_result.json').exists():
            raise RuntimeError('Ibex plan execution failed; inspect ' + str(folder / 'simulation.log'))
        tree = ET.parse(folder / 'results.xml')
        if tree.findall('.//failure') or tree.findall('.//error') or not tree.findall('.//testcase'):
            raise RuntimeError('cocotb did not pass')
        data = json.loads((folder / 'plan_result.json').read_text())
        raw = [json.loads(line) for line in artifacts.read_text(folder / 'internal_trace.jsonl').splitlines()]
        trace = [dict(cycle=row['cycle'], phase='pre_edge_effective', core_edge=bool(row['core_edge']),
                      reset_active=not row['reset_n'], events=['retirement'] if row['rvfi_valid'] else [],
                      signals={k: v for k, v in row.items() if type(v) is int}) for row in raw]
        if observers:
            if any(observer['node'] not in row['signals'] for observer in observers for row in trace):
                data['valid'], data['error'] = False, 'unavailable_observer_column'
            else:
                for row in trace:
                    row['signals'] = {p['node']: (row['signals'][p['node']] >> p.get('lsb', 0)) & ((1 << p['width']) - 1) for p in observers}
        # These fields are a projection of the complete retained raw trace, never extra DUT writes.
        receipt = dict(directory=folder.name, environment_sha256=self.environment.fingerprint,
                       plan_sha256=hashlib.sha256((folder / 'plan.json').read_bytes()).hexdigest(),
                       raw_trace_sha256=artifacts.raw_sha256(folder / 'internal_trace.jsonl'),
                       xml_pass=True, new_process=True)
        (folder / 'backend_receipt.json').write_text(json.dumps(receipt, indent=2))
        return Execution(data['valid'], data['executed_actions'], trace, set(data['monitor_hits']) if data['valid'] else set(),
                         data['cycles'], self.environment, True, data['state'], data['error'],
                         data['prefix_verified'], data['replayed_cycles'], receipt)
