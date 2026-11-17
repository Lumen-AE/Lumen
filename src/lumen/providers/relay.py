"""Operator relay: forward one untouched model response; no model provider."""
import argparse
import json
from pathlib import Path
from .client import SimulationClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--address', default='tcp://127.0.0.1:5571')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('status')
    sub.add_parser('finish-platform-validation')
    send = sub.add_parser('send')
    send.add_argument('--file', type=Path, required=True)
    args = parser.parse_args()
    wire = (args.file.read_text(encoding='utf-8') if args.command == 'send' else
            '{"__lumen_control":"' + ('status' if args.command == 'status' else 'finish_platform_validation') + '"}')
    client = SimulationClient(args.address)
    try:
        print(json.dumps(client.send_literal_json(wire), ensure_ascii=False, indent=2))
    finally:
        client.close()


if __name__ == '__main__':
    main()
