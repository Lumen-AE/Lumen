"""Append-only actual cost ledger; unknown token usage is never imputed."""
import json
from pathlib import Path
import time


class BudgetLedger:
    def __init__(self, path, *, max_cycles=None, max_model_calls=None, max_tokens=None, max_seconds=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            raise FileExistsError('Use a new ledger; do not overwrite earlier accounting')
        self.path.touch()
        self.started = time.monotonic()
        self.limits = dict(cycles=max_cycles, model_calls=max_model_calls, tokens=max_tokens, seconds=max_seconds)
        if any(value is not None and value < 0 for value in self.limits.values()):
            raise ValueError('Negative budget')
        self.cycles = self.replay_cycles = self.calls = self.tokens_known = self.unknown_usage_calls = self.attempts = 0
        self.external_preparation_seconds = 0.0

    def event(self, kind, **fields):
        with self.path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(dict(kind=kind, elapsed_seconds=time.monotonic() - self.started, **fields)) + '\n')

    def charge_model(self, usage):
        if usage is not None and (set(usage) != {'input_tokens', 'output_tokens'} or any(type(v) is not int or v < 0 for v in usage.values())):
            raise ValueError('Usage must be actual nonnegative provider counts or None')
        self.calls += 1
        if usage is None:
            self.unknown_usage_calls += 1
        else:
            self.tokens_known += sum(usage.values())
        self.event('model_call', usage=usage)

    def charge_execution(self, execution):
        if type(execution.cycles) is not int or type(execution.replayed_cycles) is not int or not 0 <= execution.replayed_cycles <= execution.cycles:
            raise ValueError('Replay cycles must be part of executed cycles')
        self.attempts += 1
        self.cycles += execution.cycles
        self.replay_cycles += execution.replayed_cycles
        self.event('execution', valid=execution.valid, cycles=execution.cycles,
                   replayed_cycles=execution.replayed_cycles, error=execution.error)

    def preparation(self, seconds, model_usage=()):
        """Charge measured preparation completed BEFORE this ledger's monotonic clock."""
        if seconds < 0:
            raise ValueError('Negative preparation time')
        self.external_preparation_seconds += seconds
        self.event('preparation', measured_seconds=seconds)
        for usage in model_usage:
            self.charge_model(usage)

    def snapshot(self):
        elapsed = time.monotonic() - self.started
        accounted = elapsed + self.external_preparation_seconds
        values = dict(cycles=self.cycles, model_calls=self.calls, tokens=self.tokens_known, seconds=accounted)
        exceeded = [key for key, limit in self.limits.items() if limit is not None and values[key] >= limit]
        # If a token cap was requested but usage is unavailable, stop with an explicit reason.
        if self.limits['tokens'] is not None and self.unknown_usage_calls:
            exceeded.append('token_budget_unverifiable')
        return dict(cycles=self.cycles, replay_cycles=self.replay_cycles, attempts=self.attempts,
                    model_calls=self.calls, known_tokens=self.tokens_known,
                    total_tokens=None if self.unknown_usage_calls else self.tokens_known,
                    unknown_usage_calls=self.unknown_usage_calls, elapsed_seconds=elapsed,
                    preparation_seconds=self.external_preparation_seconds, accounted_seconds=accounted,
                    exhausted=bool(exceeded), reasons=exceeded)
