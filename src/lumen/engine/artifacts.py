"""Lossless gzip storage for bulky evidence; callers may use the plain name."""
import gzip
import hashlib
import json
import os
from pathlib import Path


def existing(path):
    path = Path(path)
    if path.is_file():
        return path
    compressed = Path(str(path) + '.gz')
    if compressed.is_file():
        return compressed
    raise FileNotFoundError(path)


def exists(path):
    try:
        existing(path)
        return True
    except FileNotFoundError:
        return False


def open_binary(path):
    path = existing(path)
    return gzip.open(path, 'rb') if path.suffix == '.gz' else path.open('rb')


def open_text(path):
    path = existing(path)
    return gzip.open(path, 'rt', encoding='utf-8') if path.suffix == '.gz' else path.open(encoding='utf-8')


def read_text(path):
    with open_text(path) as stream:
        return stream.read()


def read_json(path):
    with open_text(path) as stream:
        return json.load(stream)


def raw_sha256(path):
    digest = hashlib.sha256()
    with open_binary(path) as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_text(path, text):
    """Write UTF-8/LF bytes atomically, replacing the previous plain artifact."""
    path = Path(path)
    destination = path if path.suffix == '.gz' else Path(str(path) + '.gz')
    temporary = Path(str(destination) + '.tmp')
    with temporary.open('wb') as output:
        with gzip.GzipFile(filename='', mode='wb', fileobj=output, compresslevel=6, mtime=0) as stream:
            stream.write(text.encode('utf-8'))
    os.replace(temporary, destination)
    if path != destination and path.exists():
        path.unlink()


def write_json(path, value):
    write_text(path, json.dumps(value, indent=2))


def append_text(path):
    """Append a gzip member; supported by standard gzip readers on Ubuntu."""
    path = Path(path)
    destination = path if path.suffix == '.gz' else Path(str(path) + '.gz')
    assert not (path != destination and path.exists()), 'initialize compressed stream first'
    return gzip.open(destination, 'at', encoding='utf-8', newline='\n', compresslevel=6)
