"""Lossless, hashed public-material batches for a fresh tested dialogue."""
import argparse
import hashlib
import json
from pathlib import Path
from lumen.paths import public_files


def pack(arm, output):
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError('Use a new empty material directory')
    parts, files = [], []
    for name, path in public_files(arm):
        data = path.read_bytes()
        remaining = data.decode('utf-8')
        pieces = []
        while remaining:
            raw = remaining.encode('utf-16-le')
            end = min(len(raw), 160000)
            while True:
                try:
                    piece = raw[:end].decode('utf-16-le')
                    break
                except UnicodeDecodeError:
                    end -= 2
            if len(raw) > 160000 and '\n' in piece:
                piece = piece[:piece.rfind('\n') + 1]
            number = len(parts) + 1
            path = output / ('part_%02d.txt' % number)
            path.write_bytes(piece.encode('utf-8'))
            parts.append(dict(part=number, file=name, bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            pieces.append(piece)
            remaining = remaining[len(piece):]
        assert ''.join(pieces).encode('utf-8') == data
        files.append(dict(file=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    groups = []
    for start in range(1, len(parts) + 1, 3):
        end = min(start + 2, len(parts))
        header = ('You are the stimulus-generating experiment participant for Lumen RTL verification. '
                  'The feedback mode is ' + arm + '. Use only the public materials and simulator feedback delivered here. '
                  'Do not invoke tools or access files, websites, commands, or other conversations. '
                  'Compute literal instruction words yourself; the controller forwards replies unchanged.\n'
                  'There are %d material parts. This message contains parts %d through %d. '
                  'Until all materials and an assigned_target arrive, reply only ACK %d-%d.\n\n' % (len(parts), start, end, start, end))
        text = header + '\n\n'.join('=== Public material %d (%s) ===\n%s' % (n, parts[n-1]['file'], (output / ('part_%02d.txt' % n)).read_text(encoding='utf-8')) for n in range(start, end+1))
        path = output / ('group_%02d.txt' % (len(groups) + 1))
        path.write_bytes(text.encode('utf-8'))
        groups.append(dict(start=start, end=end, file=path.name, bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    manifest = dict(arm=arm, files=files, parts=parts, groups=groups, complete_lossless_pack=True,
                    complete_materials_delivered=False, note='Delivery must be recorded by the controller; packing is not delivery.')
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    return dict(arm=arm, groups=len(groups), parts=len(parts), bytes=sum(f['bytes'] for f in files))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--arm', choices=('base', 'evidence'), required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(pack(args.arm, args.output)))
