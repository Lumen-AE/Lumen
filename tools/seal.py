"""Explicitly reseal a locally modified checkout; never label it an original release."""
import argparse
import ast
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Replace this checkout manifest with a local_modified seal')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = root / 'SOURCE_MANIFEST.json'
    checksum = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    catalog = checksum(root / 'targets/ibex/coverage/counted.json')
    if catalog != '619a6baaf8d33d8e4698b218ed72a3d7f25ac971c6d7058a22918c1a93d516fe':
        raise ValueError('The frozen 3832-bin catalog has changed; cannot reseal this protocol')
    directories = {'src', 'targets', 'profiles', 'workflows', 'examples', 'tests', 'tools', 'docs', 'licenses'}
    root_files = {'.gitattributes', '.gitignore', 'pyproject.toml', 'readme.md', 'requirements.txt',
                  'requirements-paper.txt', 'LICENSE'}
    rows = []
    for file in sorted(root.rglob('*')):
        relative = file.relative_to(root)
        if not file.is_file() or file.is_symlink():
            continue
        if relative.parts[0] not in directories and relative.as_posix() not in root_files:
            continue
        if any(p in ('.git', '.venv', '.build', 'build', 'dist', 'runs', '__pycache__') or p.endswith('.egg-info') for p in relative.parts):
            continue
        if file.suffix in ('.pyc', '.log'):
            continue
        if file.suffix == '.py':
            ast.parse(file.read_text(encoding='utf-8'), filename=relative.as_posix())
        rows.append(dict(path=relative.as_posix(), bytes=file.stat().st_size, sha256=checksum(file)))
    result = dict(project='Lumen', stage='local_modified',
                  previous_manifest_sha256=checksum(manifest) if manifest.exists() else None,
                  catalog_sha256=catalog, files=rows)
    if args.write:
        manifest.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(files=len(rows), written=args.write, stage='local_modified',
                          note='Local edits are not an upstream frozen release')))


if __name__ == '__main__':
    main()
