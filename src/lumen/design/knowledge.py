"""Versioned local text knowledge with explicit bin/signal/source associations."""
import hashlib
import json
from pathlib import Path
import re
import sqlite3


class KnowledgeBase:
    KINDS = {'design', 'isa', 'coverage', 'rtl'}

    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS documents(
          id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL,
          version TEXT NOT NULL, sha256 TEXT NOT NULL, text TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS links(
          document TEXT REFERENCES documents(id), entity_type TEXT, entity TEXT,
          line_start INTEGER, line_end INTEGER, UNIQUE(document,entity_type,entity,line_start,line_end));
        ''')

    def close(self):
        self.db.close()

    def ingest(self, path, kind, version, name=None):
        if kind not in self.KINDS or not version:
            raise ValueError('Knowledge requires a supported kind and explicit source version')
        path = Path(path)
        data = path.read_bytes()
        text = data.decode('utf-8')
        if '\x00' in text:
            raise ValueError('Knowledge ingestion supports UTF-8 text only')
        digest = hashlib.sha256(data).hexdigest()
        display = name or path.name
        identity = hashlib.sha256(json.dumps([display, kind, version, digest]).encode()).hexdigest()
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO documents VALUES(?,?,?,?,?,?)',
                            (identity, display, kind, version, digest, text))
        return identity

    def link(self, document, entity_type, entity, line_start=1, line_end=None):
        row = self.db.execute('SELECT text FROM documents WHERE id=?', (document,)).fetchone()
        if row is None:
            raise KeyError(document)
        count = len(row['text'].splitlines())
        line_end = count if line_end is None else line_end
        if entity_type not in ('bin', 'signal', 'node') or not 1 <= line_start <= line_end <= count:
            raise ValueError('Invalid source association')
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO links VALUES(?,?,?,?,?)',
                            (document, entity_type, entity, line_start, line_end))

    def query(self, query='', kind=None, entity_type=None, entity=None, limit=8):
        if not 1 <= limit <= 100:
            raise ValueError('Query limit must be 1..100')
        sql, args = 'SELECT DISTINCT d.* FROM documents d', []
        clauses = []
        if entity is not None:
            if entity_type not in ('bin', 'signal', 'node'):
                raise ValueError('Entity query requires an explicit entity type')
            sql += ' JOIN links l ON d.id=l.document'
            clauses += ['l.entity_type=?', 'l.entity=?']
            args += [entity_type, entity]
        if kind is not None:
            if kind not in self.KINDS:
                raise ValueError('Unknown knowledge kind')
            clauses.append('d.kind=?')
            args.append(kind)
        if clauses:
            sql += ' WHERE ' + ' AND '.join(clauses)
        terms = re.findall(r'\w+', query.casefold())
        results = []
        for row in self.db.execute(sql, args):
            lines = row['text'].splitlines()
            selected = [(i + 1, line) for i, line in enumerate(lines) if not terms or any(t in line.casefold() for t in terms)]
            if not selected:
                continue
            hits = sum(sum(line.casefold().count(t) for t in terms) for _, line in selected) if terms else 0
            results.append(dict(id=row['id'], name=row['name'], kind=row['kind'], version=row['version'],
                                sha256=row['sha256'], lexical_matches=hits, excerpts=selected[:12],
                                links=[dict(link) for link in self.db.execute('SELECT * FROM links WHERE document=?', (row['id'],))]))
        return sorted(results, key=lambda r: (-r['lexical_matches'], r['name'], r['id']))[:limit]
