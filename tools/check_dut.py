"""Resolve a DUT source manifest and run Verilator elaboration checks."""
import argparse
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', required=True)
    args = parser.parse_args()
    targets = Path(__file__).resolve().parents[1] / 'targets'
    root = (targets / args.target).resolve()
    if root.parent != targets:
        parser.error('Select one target directory name')
    config = json.loads((root / 'sources.json').read_text())
    def resolve(relative):
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.exists():
            raise ValueError('Invalid source path: ' + relative)
        return str(path)
    command = ['verilator', '--lint-only', '--timing', '-Wno-fatal', '--top-module', config['top']]
    command += ['-D' + value for value in config.get('defines', [])]
    command += ['-G' + key + '=' + str(value) for key, value in config.get('parameters', {}).items()]
    command += ['-I' + resolve(value) for value in config.get('include_dirs', [])]
    command += [resolve(value) for value in config['files']]
    subprocess.run(command, cwd=root, check=True)
    print(json.dumps(dict(target=args.target, passed=True, check='Verilator elaboration', files=len(config['files']))))


if __name__ == '__main__':
    main()
