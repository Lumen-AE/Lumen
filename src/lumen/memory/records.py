"""Explicit compatibility and fresh-process checks for input-prefix reuse."""
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from lumen.engine.interfaces import Execution
from lumen.reasoning.temporal import Condition


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode('utf-8')).hexdigest()


class ExperienceStore:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS experience(id INTEGER PRIMARY KEY, target TEXT, success INTEGER, data TEXT)')

    def add(self, target, execution, evidence):
        successful = execution.valid and target in execution.monitor_hits
        data = dict(target=target, success=successful, valid=execution.valid, error=execution.error,
                    environment=execution.environment.fingerprint, cycles=execution.cycles,
                    evidence=evidence, monitor_hits=sorted(execution.monitor_hits), recorded_ns=time.time_ns())
        with self.db:
            cursor = self.db.execute('INSERT INTO experience(target,success,data) VALUES(?,?,?)', (target, int(successful), json.dumps(data)))
        return cursor.lastrowid

    def find(self, target, limit=8):
        if not 1 <= limit <= 100:
            raise ValueError('Limit must be 1..100')
        return [json.loads(r[0]) for r in self.db.execute('SELECT data FROM experience WHERE target=? ORDER BY id DESC LIMIT ?', (target, limit))]

    def close(self):
        self.db.close()


class PrefixStore:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.directory / 'prefixes.sqlite')
        self.db.execute('CREATE TABLE IF NOT EXISTS prefixes(id TEXT PRIMARY KEY, environment TEXT, data TEXT)')

    def store(self, execution, arrival, target, *, complete_preparation=True):
        if not execution.valid or not execution.fresh_process or not complete_preparation:
            raise ValueError('A prefix requires valid execution from the declared fresh initial state and its complete preparation')
        if not execution.actions or not execution.trace or not execution.backend_receipt:
            raise ValueError('A verified prefix requires actions, measured trace and backend receipt')
        if not arrival or any(c.offset != 0 or c.holds(execution.state) is not True for c in arrival):
            raise ValueError('Arrival conditions must be measured and true at the recorded action boundary')
        record = dict(schema=1, environment=asdict(execution.environment), environment_sha256=execution.environment.fingerprint,
                      actions=execution.actions, arrival=[asdict(c) for c in arrival], target=target,
                      target_hit=target in execution.monitor_hits, monitor_hits=sorted(execution.monitor_hits),
                      start='declared_fresh_process', end='after_last_complete_action',
                      cycles=execution.cycles, state=execution.state, trace_sha256=digest(execution.trace),
                      backend_receipt=execution.backend_receipt)
        identity = digest(record)
        evidence = self.directory / (identity + '.trace.json.gz')
        if not evidence.exists():
            with gzip.open(evidence, 'wt', encoding='utf-8') as stream:
                json.dump(execution.trace, stream)
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO prefixes VALUES(?,?,?)', (identity, execution.environment.fingerprint, json.dumps(record)))
        return identity

    def get(self, identity):
        row = self.db.execute('SELECT data FROM prefixes WHERE id=?', (identity,)).fetchone()
        if row is None:
            raise KeyError(identity)
        record = json.loads(row[0])
        if digest(record) != identity:
            raise ValueError('Prefix record integrity mismatch')
        with gzip.open(self.directory / (identity + '.trace.json.gz'), 'rt', encoding='utf-8') as stream:
            if digest(json.load(stream)) != record['trace_sha256']:
                raise ValueError('Prefix evidence integrity mismatch')
        return dict(id=identity, **record)

    def compatible(self, environment, required=()):
        required = {(c.signal, c.op, c.value) for c in required}
        results = []
        for row in self.db.execute('SELECT id FROM prefixes WHERE environment=? ORDER BY id', (environment.fingerprint,)):
            record = self.get(row[0])
            available = {(c['signal'], c['op'], c['value']) for c in record['arrival']}
            if required <= available:
                results.append(record)
        return sorted(results, key=lambda r: (r['cycles'], r['id']))

    def replay(self, identity, backend, suffix, observers=()):
        record = self.get(identity)
        if record['environment_sha256'] != backend.environment.fingerprint:
            return Execution(False, [], [], set(), 0, backend.environment, False, error='prefix_environment_mismatch')
        result = backend.execute(suffix, prefix=record, observers=observers)
        if result.environment.fingerprint != record['environment_sha256'] or not result.fresh_process:
            result.valid, result.error = False, 'replay_not_from_declared_initial_state'
            result.monitor_hits = set()
        if not result.prefix_verified:
            result.valid, result.error = False, result.error or 'prefix_arrival_mismatch'
            result.monitor_hits = set()
        return result

    def close(self):
        self.db.close()
