"""Real RTL calibration: malformed replies, arm filtering and trace recount."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from lumen.paths import ROOT
from lumen.providers.client import SimulationClient
from lumen.engine import artifacts
from lumen.coverage.recount import audit


def run(arm, port, root, reference=None):
    output = root / arm
    address = 'tcp://127.0.0.1:' + str(port)
    with (root / (arm + '_launcher.log')).open('w') as log:
        proc = subprocess.Popen(['bash', str(ROOT / 'tools/run.sh'), '--arm', arm, '--output', str(output),
                                 '--bind', address, '--platform-validation'], stdout=log, stderr=subprocess.STDOUT)
        client = None
        try:
            start = time.monotonic()
            while not (output / 'ready.json').exists():
                if proc.poll() is not None:
                    raise RuntimeError('Startup failed: ' + str(output))
                if time.monotonic() - start > 240:
                    raise TimeoutError('RTL did not become ready')
                time.sleep(0.1)
            client = SimulationClient(address, timeout_ms=30000)
            status = client.send_literal_json('{"__lumen_control":"status"}')
            initial = status['assigned_target']['id']
            first = client.send_literal_json('not JSON')
            second = client.send_literal_json('not JSON')
            assert first['decision']['target'] == initial
            assert first['error'] and second['error']
            assert second['decision']['advance']
            action = dict(target=second['assigned_target']['id'], cycles=256, reset=True,
                          words=[[0x100080, 0x13], [0x100084, 0x6f]])
            third = client.send_literal_json(json.dumps(action))
            assert not third.get('error')
            assert ('evidence' in third) == (arm == 'evidence')
            if arm == 'evidence':
                assert third['evidence']['selector'] == 'official_source_probe_dependencies'
                assert 0 < len(third['evidence']['trace']) <= 64
            client.send_literal_json('{"__lumen_control":"finish_platform_validation"}')
            assert proc.wait(timeout=60) == 0
            recount = audit(output)
            assert recount['passed'] and recount['rows'] == 776
            result = dict(arm=arm, passed=True, actions=3, model_calls=0, recount=recount)
            if reference:
                original = reference / arm
                assert artifacts.read_text(original / 'internal_trace.jsonl') == artifacts.read_text(output / 'internal_trace.jsonl'), 'migration changed a raw sample'
                assert artifacts.read_json(original / 'report.json')['primary'] == artifacts.read_json(output / 'report.json')['primary']
                result['original_trace_and_counts_identical'] = True
            (output / 'platform_test.json').write_text(json.dumps(result, indent=2))
            print(json.dumps(result), flush=True)
            return result
        finally:
            if client:
                client.close()
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=15)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--reference', type=Path)
    p.add_argument('--port', type=int, default=5673)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = [run(arm, args.port + i, args.output.resolve(), args.reference) for i, arm in enumerate(('base', 'evidence'))]
    (args.output / 'receipt.json').write_text(json.dumps(results, indent=2))
