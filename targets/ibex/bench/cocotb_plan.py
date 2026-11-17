"""Optional declared-start input replay; separate from the historical live session."""
import json
import os
from pathlib import Path
import cocotb
from cocotb.triggers import Timer
from ibex_runtime import LumenRuntime


def boundary(runtime):
    return {k: v for k, v in dict(last_pc=runtime.last_pc, last_instruction=runtime.last_instruction,
                                 cycle=runtime.cycle).items() if v is not None}


@cocotb.test()
async def execute_declared_plan(dut):
    request = json.loads(Path(os.environ['LUMEN_PLAN']).read_text())
    output = Path(os.environ['LUMEN_OUTPUT'])
    dut.clk_i.value = 0
    dut.rst_ni.value = 1
    await Timer(1, units='ns')
    dut.rst_ni.value = 0
    await Timer(1, units='ns')
    runtime = LumenRuntime(dut, 'evidence')
    await runtime.reset()
    prefix_length = request['prefix_length']
    executed, error, verified, replay_cycles = [], None, False, 0
    try:
        for index, action in enumerate(request['actions']):
            await runtime.action(action)
            executed.append(action)
            if prefix_length and index + 1 == prefix_length:
                state = boundary(runtime)
                verified = all(state.get(c['signal']) is not None and
                               ((state[c['signal']] == c['value']) if c['op'] == 'eq' else (state[c['signal']] != c['value']))
                               for c in request['arrival'])
                replay_cycles = runtime.cycle
                (output / 'prefix_boundary.json').write_text(json.dumps(dict(state=state, arrival=request['arrival'], verified=verified), indent=2))
                if not verified:
                    error = 'prefix_arrival_mismatch'
                    break  # No suffix action may execute after a failed arrival check.
    except (ValueError, TypeError, KeyError) as exc:
        error = type(exc).__name__ + ': ' + str(exc)
    runtime.termination = error or 'declared_plan_complete'
    runtime.save_audit(output)
    report = runtime.primary_report()
    (output / 'plan_result.json').write_text(json.dumps(dict(valid=error is None, error=error,
        executed_actions=executed, cycles=runtime.cycle, state=boundary(runtime),
        prefix_verified=verified, replayed_cycles=replay_cycles,
        monitor_hits=[key for key, count in report['counts'].items() if count],
        complete_preparation=True), indent=2))
