"""Start real RTL, send public materials to an API, relay literal completions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from lumen.paths import ROOT, public_files
from lumen.providers.client import SimulationClient
from lumen.providers.openai_compatible import ChatCompletions


def initial_messages(arm):
    messages = [dict(role='system', content=(
        'You generate Lumen Ibex simulation stimuli. All public materials are supplied below. '
        'Use only these materials and measured feedback. Do not use tools. '
        'Return one literal JSON action after assigned_target; no Markdown or repair by the controller.'))]
    materials = []
    for name, path in public_files(arm):
        data = path.read_bytes()
        messages.append(dict(role='user', content='=== ' + name + ' ===\n' + data.decode('utf-8')))
        materials.append(dict(file=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    return messages, materials


def run(args):
    provider = ChatCompletions(args.model, args.base_url, args.key_env, args.reasoning_effort,
                               args.max_completion_tokens, args.timeout, args.local_fixture)
    if args.local_fixture and not args.smoke_rounds:
        raise ValueError('Local fixtures require a positive smoke limit')
    if args.smoke_rounds < 0 or (args.seed and (args.arm != 'evidence' or args.smoke_rounds)):
        raise ValueError('Seed is allowed only for a complete evidence experiment')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError('Use a new empty output directory')
    metadata = provider.metadata()
    (output / 'provider.json').write_text(json.dumps(metadata, indent=2))
    messages, materials = initial_messages(args.arm)
    (output / 'materials_manifest.json').write_text(json.dumps(materials, indent=2))
    sim = output / 'simulation'
    cmd = [sys.executable, '-B', '-m', 'lumen.commands.serve', '--arm', args.arm,
           '--output', str(sim), '--bind', args.bind, '--provider-config', str(output / 'provider.json')]
    if args.smoke_rounds:
        cmd.extend(['--smoke-rounds', str(args.smoke_rounds)])
    if args.seed:
        cmd.extend(['--seed', str(args.seed.resolve())])
    environment = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1')
    environment.pop(args.key_env, None)
    client, proc = None, None
    events = []
    completed = False
    started = time.monotonic()
    with (output / 'launcher.log').open('w') as launcher, (output / 'api_events.jsonl').open('x') as journal:
        def event(**row):
            journal.write(json.dumps(row, ensure_ascii=False) + '\n')
            journal.flush()
            events.append(row)
        try:
            proc = subprocess.Popen(cmd, stdout=launcher, stderr=subprocess.STDOUT,
                                    env=environment, start_new_session=True)
            deadline = time.monotonic() + args.startup_timeout
            while not (sim / 'ready.json').exists():
                if proc.poll() is not None:
                    raise RuntimeError('RTL startup failed; inspect simulation/simulation.log')
                if time.monotonic() >= deadline:
                    raise TimeoutError('RTL startup timeout')
                time.sleep(0.1)
            client = SimulationClient(args.bind, timeout_ms=120000)
            feedback = client.send_literal_json('{"__lumen_control":"status"}')
            messages.append(dict(role='user', content=json.dumps(feedback, ensure_ascii=False)))
            number = 0
            while feedback.get('assigned_target') is not None:
                number += 1
                # Full messages are saved, including the original public source and every feedback.
                # The journal records dispatch before sending so failures cannot be called zero cost.
                request_text = json.dumps(messages, ensure_ascii=False)
                (output / f'messages_{number:04}.json').write_text(request_text, encoding='utf-8')
                event(kind='request_dispatched', round=number,
                      messages_sha256=hashlib.sha256(request_text.encode('utf-8')).hexdigest())
                answer = provider.complete(messages)
                wire = answer.text.encode('utf-8')
                (output / f'reply_{number:04}.txt').write_bytes(wire)
                event(kind='completion_received', round=number, response_id=answer.response_id,
                      wire_sha256=hashlib.sha256(wire).hexdigest(), usage=answer.usage,
                      finish_reason=answer.finish_reason)
                # Reserved control commands must never be usable as model-generated actions.
                if answer.text in ('{"__lumen_control":"status"}', '{"__lumen_control":"finish_platform_validation"}'):
                    raise ValueError('Model returned a reserved transport control command')
                feedback = client.send_literal_json(answer.text)
                (output / f'feedback_{number:04}.json').write_text(json.dumps(feedback, indent=2))
                event(kind='rtl_response_received', round=number, error=feedback.get('error'))
                messages.extend([dict(role='assistant', content=answer.text),
                                 dict(role='user', content=json.dumps(feedback, ensure_ascii=False))])
                if feedback.get('denominator_valid') is False:
                    raise RuntimeError('Actual RTL contradicted an excluded bin; inspect simulation audit')
                if feedback.get('smoke_complete') or feedback.get('coverage', {}).get('finished'):
                    break
            if feedback.get('assigned_target') is None and number == 0:
                # An already-complete seed has no model work; make the simulator flush its audit.
                client.send_literal_json('{}')
            if proc.wait(timeout=60) != 0:
                raise RuntimeError('RTL did not complete successfully')
            completed = True
        finally:
            if client:
                client.close()
            if proc and proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=10)
            dispatches = sum(e['kind'] == 'request_dispatched' for e in events)
            responses = [e for e in events if e['kind'] == 'completion_received']
            unknown = sum(e['usage'] is None for e in responses)
            unknown_outcomes = dispatches - len(responses)
            known = sum(e['usage']['total_tokens'] for e in responses if e['usage'] is not None)
            summary = dict(completed=completed, provider=metadata['model']['provider'],
                           api_requests_dispatched=dispatches, completions_received=len(responses),
                           unknown_outcome_requests=unknown_outcomes, unknown_usage_calls=unknown,
                           known_tokens=known, total_tokens=None if unknown or unknown_outcomes else known,
                           elapsed_seconds=time.monotonic() - started,
                           new_model_calls=0 if args.local_fixture else len(responses),
                           model_call_count_complete=not bool(unknown_outcomes),
                           local_protocol_fixture=args.local_fixture,
                           simulation_directory='simulation', automatic_retries=0)
            (output / 'api_summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--arm', choices=('base', 'evidence'), required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--base-url', default='https://api.openai.com/v1')
    p.add_argument('--key-env', default='OPENAI_API_KEY')
    p.add_argument('--reasoning-effort')
    p.add_argument('--max-completion-tokens', type=int)
    p.add_argument('--timeout', type=float, default=180)
    p.add_argument('--startup-timeout', type=float, default=300)
    p.add_argument('--smoke-rounds', type=int, default=0)
    p.add_argument('--bind', default='tcp://127.0.0.1:5673')
    p.add_argument('--seed', type=Path)
    p.add_argument('--local-fixture', action='store_true', help='Loopback-only offline HTTP fixture; not a model experiment')
    run(p.parse_args())


if __name__ == '__main__':
    main()
