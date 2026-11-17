"""Offline API protocol + actual RTL, including a deliberately malformed reply."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from lumen.coverage.recount import audit
from lumen.paths import ROOT
from tests.api_fixture import http_fixture, stimulus


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--port', type=int, default=5697)
    args = p.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for index, arm in enumerate(('base', 'evidence')):
        directory = output / arm
        with http_fixture(stimulus) as (url, calls):
            with (output / (arm + '.log')).open('w') as log:
                result = subprocess.run([sys.executable, '-B', '-m', 'lumen.commands.api',
                    '--arm', arm, '--output', str(directory), '--model', 'local-protocol-fixture',
                    '--base-url', url, '--local-fixture', '--smoke-rounds', '2',
                    '--bind', 'tcp://127.0.0.1:' + str(args.port + index)],
                    env=dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1'),
                    stdout=log, stderr=subprocess.STDOUT, timeout=420)
            assert result.returncode == 0, 'Inspect ' + str(output / (arm + '.log'))
        assert len(calls) == 2
        assert all(call['authorization'] is None for call in calls)
        history = calls[1]['payload']['messages']
        wire1 = (directory / 'reply_0001.txt').read_text()
        assert history[-2]['role'] == 'assistant' and history[-2]['content'] == wire1
        assert json.loads(history[-1]['content']) == json.loads((directory / 'feedback_0001.json').read_text())
        events = [json.loads(line) for line in (directory / 'api_events.jsonl').read_text().splitlines()]
        audit_rows = [json.loads(line) for line in (directory / 'simulation/controller_audit.jsonl').read_text().splitlines()]
        for number, row in enumerate(audit_rows, 1):
            wire = (directory / f'reply_{number:04}.txt').read_bytes()
            assert row['wire'] == wire.decode('utf-8')
            assert row['wire_sha256'] == hashlib.sha256(wire).hexdigest()
        assert len(audit_rows) == 2
        first = json.loads((directory / 'feedback_0001.json').read_text())
        second = json.loads((directory / 'feedback_0002.json').read_text())
        assert not first.get('error') and second.get('error') and second['smoke_complete']
        assert ('evidence' in first) == (arm == 'evidence')
        summary = json.loads((directory / 'api_summary.json').read_text())
        assert summary['completed'] and summary['new_model_calls'] == 0
        assert summary['api_requests_dispatched'] == summary['completions_received'] == 2
        assert summary['unknown_usage_calls'] == 1 and summary['total_tokens'] is None
        assert summary['known_tokens'] == 34 and summary['automatic_retries'] == 0
        trial = json.loads((directory / 'simulation/trial_summary.json').read_text())
        assert trial['model']['provider'] == 'local_http_fixture'
        assert trial['submitted_model_responses'] == trial['model_calls'] == 0
        recount = audit(directory / 'simulation')
        assert recount['passed'] and recount['rows'] >= 512
        results.append(dict(arm=arm, passed=True, real_rtl=True, local_http_requests=2,
                            new_model_calls=0, malformed_reply_preserved_and_charged=True,
                            complete_history=True, unknown_usage_preserved=True, recount=recount))
        print(arm + ' API protocol/RTL PASS', flush=True)
    (output / 'receipt.json').write_text(json.dumps(dict(passed=True, paid_api_verified=False, stages=results), indent=2))


if __name__ == '__main__':
    main()
