"""Re-execute saved P1 literal replies in real RTL; never call a model provider."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from lumen.paths import ROOT
from lumen.engine import artifacts
from lumen.providers.client import SimulationClient
from lumen.coverage.recount import audit


def run(arm, reference, output, port):
    prior = reference / (arm + '_sim')
    wires = [json.loads(line) for line in (prior / 'controller_audit.jsonl').read_text().splitlines()]
    assert len(wires) == 2, 'This regression case expects the two saved P1 smoke replies'
    destination = output / arm
    address = 'tcp://127.0.0.1:' + str(port)
    with (output / (arm + '_launcher.log')).open('w') as log:
        # Calibration semantics: these are saved replies, not new model calls.
        proc = subprocess.Popen(['bash', str(ROOT / 'tools/run.sh'), '--arm', arm,
                                 '--output', str(destination), '--bind', address,
                                 '--platform-validation'], stdout=log, stderr=subprocess.STDOUT)
        client = None
        try:
            start = time.monotonic()
            while not (destination / 'ready.json').exists():
                if proc.poll() is not None:
                    raise RuntimeError('Startup failed; inspect ' + str(destination / 'simulation.log'))
                if time.monotonic() - start > 240:
                    raise TimeoutError('RTL did not become ready')
                time.sleep(0.1)
            client = SimulationClient(address, timeout_ms=30000)
            status = client.send_literal_json('{"__lumen_control":"status"}')
            receipts = []
            for number, old in enumerate(wires, 1):
                wire = (reference / f'{arm}_reply_{number:03}.txt').read_bytes().decode('utf-8')
                digest = hashlib.sha256(wire.encode('utf-8')).hexdigest()
                assert wire == old['wire'] and digest == old['wire_sha256']
                assert json.loads(wire)['target'] == status['assigned_target']['id']
                actual = client.send_literal_json(wire)
                assert not actual.get('error'), actual
                expected = json.loads((reference / f'{arm}_receipt_{number:03}.json').read_text())['feedback']
                # Only the external stop mode differs; all measured/public data must match.
                expected = {k: v for k, v in expected.items() if k not in ('smoke_complete', 'run_stop_reason')}
                assert actual == expected, ('public feedback changed', arm, number)
                assert ('evidence' in actual) == (arm == 'evidence')
                receipts.append(dict(round=number, wire_sha256=digest, feedback=actual))
                status = actual
            client.send_literal_json('{"__lumen_control":"finish_platform_validation"}')
            assert proc.wait(timeout=60) == 0
            assert artifacts.read_text(prior / 'internal_trace.jsonl') == artifacts.read_text(destination / 'internal_trace.jsonl'), 'raw RTL sample changed'
            assert artifacts.read_json(prior / 'report.json')['primary'] == artifacts.read_json(destination / 'report.json')['primary'], 'per-bin counts changed'
            assert artifacts.read_text(prior / 'actions_and_feedback.jsonl') == artifacts.read_text(destination / 'actions_and_feedback.jsonl'), 'action feedback changed'
            assert artifacts.read_json(prior / 'first_hit_witnesses.json') == artifacts.read_json(destination / 'first_hit_witnesses.json'), 'first-hit witness changed'
            for name in ('controller_audit.jsonl', 'target_outcomes.json', 'covered_bins.json', 'stage_covered_bins.json'):
                assert (prior / name).read_bytes() == (destination / name).read_bytes(), name
            summary = json.loads((destination / 'trial_summary.json').read_text())
            assert summary['model_calls'] == summary['submitted_model_responses'] == 0
            assert summary['run_kind'] == 'platform_validation'
            recount = audit(destination)
            result = dict(arm=arm, passed=True, input_origin='saved P1 gpt-5.6-luna literal replies',
                          new_model_calls=0, actions=len(wires), raw_replies_unchanged=True,
                          public_feedback_identical=True, all_bin_counts_identical=True,
                          raw_cycle_trace_identical=True, first_hit_witnesses_identical=True,
                          controller_outcomes_identical=True, recount=recount,
                          evidence_rows=[len(r['feedback']['evidence']['trace']) for r in receipts if 'evidence' in r['feedback']])
            (destination / 'replay_receipts.json').write_text(json.dumps(receipts, indent=2))
            (destination / 'replay_test.json').write_text(json.dumps(result, indent=2))
            print(json.dumps(result), flush=True)
            return result
        finally:
            if client:
                client.close()
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=15)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--port', type=int, default=5693)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    results = [run(arm, args.reference.resolve(), args.output.resolve(), args.port + i)
               for i, arm in enumerate(('base', 'evidence'))]
    (args.output / 'receipt.json').write_text(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
