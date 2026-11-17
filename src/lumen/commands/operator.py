"""Lumen command-line operator. Text transport never generates model actions."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from lumen.commands.preflight import ROOT, check
from lumen.providers.client import SimulationClient


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('preflight')
    for name in ('status', 'send', 'finish-platform-validation'):
        q = sub.add_parser(name)
        q.add_argument('--address', default='tcp://127.0.0.1:5671')
        q.add_argument('--receipt', type=Path)
        if name == 'send':
            q.add_argument('--file', type=Path, required=True)
    q = sub.add_parser('audit')
    q.add_argument('--run', type=Path, required=True)
    args = p.parse_args()
    if args.command == 'preflight':
        result = check()
    elif args.command == 'audit':
        from lumen.coverage.recount import audit
        result = audit(args.run.resolve())
    else:
        if args.receipt and args.receipt.exists():
            p.error('Receipt already exists; reconcile the previous execution before submitting again.')
        wire = args.file.read_bytes().decode('utf-8') if args.command == 'send' else (
            '{"__lumen_control":"status"}' if args.command == 'status' else
            '{"__lumen_control":"finish_platform_validation"}')
        client = SimulationClient(args.address, timeout_ms=30000)
        try:
            result = client.send_literal_json(wire)
        finally:
            client.close()
        if args.receipt:
            args.receipt.parent.mkdir(parents=True, exist_ok=True)
            args.receipt.write_text(json.dumps(dict(wire_sha256=hashlib.sha256(wire.encode()).hexdigest(), feedback=result), ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
