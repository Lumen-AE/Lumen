"""Persistent LUMEN relay. It accepts literal actions and never invokes an LLM."""
import hashlib
import json
import os
from pathlib import Path

import cocotb
from cocotb.triggers import Timer
import zmq

from lumen.engine.actions import validate
from ibex_memory import Memory
from ibex_runtime import LumenRuntime
from lumen.engine.scheduler import TargetController
from lumen.engine.config import load_config
from lumen.engine.feedback import public_feedback
from lumen.paths import COVERAGE


@cocotb.test()
async def lumen_live(dut):
    config, catalog = load_config(os.environ.get('LUMEN_EXPERIMENT_CONFIG'))
    assert os.environ['LUMEN_PROFILE'] == config['profile']
    assert os.environ['LUMEN_CATALOG'] == config['catalog']
    requested_arm = os.environ.get('LUMEN_ARM', 'base')
    assert requested_arm in ('base', 'baseline', 'evidence')
    arm = 'baseline' if requested_arm == 'base' else requested_arm
    dut.clk_i.value = 0
    dut.rst_ni.value = 1
    await Timer(1, units='ns')
    dut.rst_ni.value = 0
    await Timer(1, units='ns')
    runtime = LumenRuntime(dut, arm)
    records = {r['id']: {k: r[k] for k in ('id', 'declaration', 'group', 'instance', 'bin', 'file', 'line')} for r in catalog['targets']}
    seed_path = os.environ.get('LUMEN_COVERAGE_SEED')
    seed = json.loads(Path(seed_path).read_text()) if seed_path else {}
    if seed:
        assert arm == 'evidence', 'only evidence may start from baseline coverage'
        assert seed['catalog_sha256'] == config['catalog_sha256'], 'baseline catalog changed'
        assert seed['baseline_completed'], 'baseline must finish before evidence'
    controller = TargetController(list(records), config['consecutive_target_misses'], seed.get('covered_ids', []))
    formal = config.get('formal_llm_enabled', False)
    run_kind = config.get('run_kind', 'experiment')
    smoke_limit = config.get('smoke_max_responses', 0)
    assert run_kind in ('experiment', 'smoke', 'platform_validation')
    assert isinstance(smoke_limit, int) and smoke_limit >= 0
    assert (run_kind == 'smoke') == (smoke_limit > 0)
    assert not (seed and run_kind == 'smoke'), 'smoke stages are independent and cannot consume a formal seed'
    output = Path(os.environ['LUMEN_OUTPUT'])
    output.mkdir(parents=True, exist_ok=True)
    runtime.enable_streaming(output)
    (output / 'controller_audit.jsonl').write_text('')
    budget = config['cycles_per_attempt']
    excluded_path=COVERAGE/'excluded.json'
    excluded={r['target']['id'] for r in json.loads(excluded_path.read_text())}

    async def prepare_target():
        runtime.imem = Memory(dut, 'instr')
        runtime.dmem = Memory(dut, 'data')
        await runtime.reset()

    await prepare_target()
    feedback = dict(coverage=runtime.primary_report(), new_bins=[])
    reply = public_feedback(feedback, controller, records, arm)
    address = os.environ.get('LUMEN_BIND', 'tcp://127.0.0.1:5571')
    try:
        with zmq.Context() as context:
            with context.socket(zmq.REP) as socket:
                socket.setsockopt(zmq.LINGER, 0)
                socket.bind(address)
                (output / 'ready.json').write_text(json.dumps(dict(address=address, arm=arm, model_calls=0, config=config)))
                while True:
                    wire = socket.recv().decode('utf-8', errors='replace')
                    if wire == '{"__lumen_control":"status"}':
                        socket.send_json(reply)
                        continue
                    if wire == '{"__lumen_control":"finish_platform_validation"}':
                        if formal:
                            socket.send_json(dict(error='formal trial cannot finish via platform-validation command',coverage=controller.report()))
                            continue
                        runtime.termination = 'operator_finished_platform_validation'
                        socket.send_json(dict(finished=True, model_calls=0, coverage=controller.report()))
                        break
                    if controller.finished:
                        socket.send_json(dict(finished=True, stop_reason=controller.stop_reason, coverage=controller.report()))
                        break
                    assigned = controller.current
                    try:
                        action = json.loads(wire)
                        checked = validate(action, max_cycles=budget)
                        if checked['target'] != assigned:
                            raise ValueError('action target must equal the assigned target')
                        if checked['cycles'] != budget:
                            raise ValueError('cycles must equal the fixed attempt budget')
                        feedback = await runtime.action(action, max_cycles=budget)
                    except (ValueError, TypeError, KeyError) as exc:
                        feedback = await runtime.reject(wire, exc, budget)
                    contradictions=sorted(excluded & set(runtime.coverage.all_hits))
                    if contradictions:
                        runtime.termination='reachability_exclusion_contradicted'
                        failure=dict(finished=True,denominator_valid=False,
                                     error=runtime.termination,bins=contradictions,
                                     cycle=runtime.cycle,wire=wire)
                        (output/'excluded_bin_contradiction.json').write_text(json.dumps(failure,indent=2))
                        socket.send_json(failure)
                        break
                    decision = controller.accept(feedback)
                    with (output / 'controller_audit.jsonl').open('a') as stream:
                        stream.write(json.dumps(dict(wire=wire, wire_sha256=hashlib.sha256(wire.encode('utf-8')).hexdigest(), decision=decision, union=controller.report())) + '\n')
                    runtime.flush_stream()
                    (output / 'controller_state.json').write_text(json.dumps(controller.report(), indent=2))
                    if decision['advance'] and not controller.finished:
                        await prepare_target()
                    reply = public_feedback(feedback, controller, records, arm, decision)
                    smoke_done = run_kind == 'smoke' and controller.rounds >= smoke_limit
                    if smoke_done:
                        reply['smoke_complete'] = True
                        reply['run_stop_reason'] = 'smoke_response_limit'
                    socket.send_json(reply)
                    if controller.finished:
                        runtime.termination = controller.stop_reason
                        break
                    if smoke_done:
                        runtime.termination = 'smoke_response_limit'
                        break
    finally:
        runtime.save_audit(output)
        (output / 'controller_audit.json').write_text(json.dumps(dict(
            format='jsonl', file='controller_audit.jsonl', records=controller.rounds), indent=2))
        (output / 'target_outcomes.json').write_text(json.dumps(controller.records, indent=2))
        (output / 'covered_bins.json').write_text(json.dumps(sorted(controller.union), indent=2))
        (output / 'stage_covered_bins.json').write_text(json.dumps(sorted(controller.stage_hits), indent=2))
        (output / 'trial_summary.json').write_text(json.dumps(dict(
            **controller.report(), arm=arm, catalog=config['catalog'], model_calls=None if formal else 0,
            run_kind=run_kind, smoke_complete=run_kind == 'smoke' and controller.rounds >= smoke_limit,
            provider_calls_by_simulator=0, submitted_model_responses=controller.rounds if formal else 0,
            model=config.get('model'), model_context_policy=config.get('model_context_policy'),
            covered_ids_file='covered_bins.json', stage_covered_ids_file='stage_covered_bins.json',
            catalog_sha256=config['catalog_sha256'],
            scoring=config['scoring'], termination=runtime.termination,
            denominator_valid=runtime.termination!='reachability_exclusion_contradicted'), indent=2))
    assert runtime.termination!='reachability_exclusion_contradicted', 'Excluded bin hit; saved trace invalidates the denominator and requires re-audit'
