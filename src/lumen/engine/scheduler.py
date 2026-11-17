"""Assigned-target scheduling and measured cumulative union."""

class TargetController:
    def __init__(self, targets, misses=2, initial_covered=()):
        self.targets = list(targets)
        if len(set(self.targets)) != len(self.targets):
            raise ValueError('duplicate target IDs')
        self.limit = misses
        self.initial_covered = set(initial_covered)
        if not self.initial_covered <= set(self.targets):
            raise ValueError('initial coverage contains an unknown bin')
        self.union = set(self.initial_covered)
        self.stage_hits = set()
        self.index = 0
        self.misses = 0
        self.attempts = 0
        self.records = []
        self.rounds = 0
        self.finished = False
        self.stop_reason = None
        self._select()

    @property
    def current(self):
        return None if self.finished else self.targets[self.index]

    def _select(self):
        while self.index < len(self.targets) and self.targets[self.index] in self.union:
            self.records.append(dict(target=self.targets[self.index], outcome='already_covered', attempts=0))
            self.index += 1
        if self.index == len(self.targets):
            self.finished = True
            self.stop_reason = 'all_bins_covered' if len(self.union) == len(self.targets) else 'all_targets_attempted'

    def accept(self, feedback):
        if self.finished:
            raise ValueError('trial already finished')
        current = self.current
        self.rounds += 1
        self.attempts += 1
        counts = feedback['coverage']['counts']
        if set(counts) != set(self.targets):
            raise ValueError('feedback catalog differs from the frozen target set')
        before = set(self.union)
        self.stage_hits.update(k for k, value in counts.items() if value)
        self.union.update(self.stage_hits)
        hit = current in self.union
        self.misses = 0 if hit else self.misses + 1
        advance = hit or self.misses >= self.limit
        decision = dict(target=current, assigned_target_hit=hit, attempt=self.attempts,
                        consecutive_target_misses=self.misses, incidental_new_bins=sorted((self.union - before) - {current}),
                        advance=advance)
        if advance:
            self.records.append(dict(target=current, outcome='hit' if hit else 'two_target_misses', attempts=self.attempts))
            self.index += 1
            self.misses = self.attempts = 0
            self._select()
        return decision

    def report(self):
        total = len(self.targets)
        return dict(hit=len(self.union), total=total, percent=100 * len(self.union) / total if total else 0,
                    initial_hit=len(self.initial_covered), stage_hit=len(self.stage_hits),
                    additional_hit=len(self.stage_hits-self.initial_covered),
                    rounds=self.rounds, current_target=self.current, consecutive_target_misses=self.misses,
                    finished=self.finished, stop_reason=self.stop_reason)


