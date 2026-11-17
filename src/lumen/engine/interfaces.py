"""Optional paper-workflow contracts; the historical live runner does not import these."""
from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Protocol


@dataclass(frozen=True)
class Environment:
    design_sha256: str
    coverage_sha256: str
    parameters: dict
    initial_state: dict
    memory_and_responses: dict
    seed: int | None

    @property
    def fingerprint(self):
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


@dataclass
class Execution:
    valid: bool
    actions: list
    trace: list
    monitor_hits: set
    cycles: int
    environment: Environment
    fresh_process: bool
    state: dict = field(default_factory=dict)
    error: str | None = None
    prefix_verified: bool = False
    replayed_cycles: int = 0
    backend_receipt: dict = field(default_factory=dict)


@dataclass
class Generation:
    actions: list
    # One entry per actual model call. None means provider usage was unavailable.
    usage: list = field(default_factory=list)
    prefix_id: str | None = None


class Generator(Protocol):
    def generate(self, context: dict) -> Generation: ...


class Backend(Protocol):
    environment: Environment

    def execute(self, actions: list, *, prefix=None, observers=()) -> Execution: ...


class Judge(Protocol):
    def evaluate(self, target, execution: Execution, previous=()) -> dict: ...


class Scheduler(Protocol):
    def next_target(self, covered: set) -> str | None: ...
