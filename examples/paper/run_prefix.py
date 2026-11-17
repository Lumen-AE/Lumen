"""Real full-Ibex prefix replay and optional Initial/Refine integration example."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import time
from lumen.paths import FCOV
from lumen.engine.ibex_batch import IbexBatchBackend
from lumen.engine.interfaces import Generation
from lumen.engine.budget import BudgetLedger
from lumen.engine.paper import run_two_pass
from lumen.coverage.recount import audit
from lumen.design.knowledge import KnowledgeBase
from lumen.memory.records import ExperienceStore, PrefixStore
from lumen.observation.comparison import EvidenceJudge
from lumen.reasoning.temporal import Condition, Goal


ALU = 'uarch_cg/cp_id_instr_category/0'
MUL = 'uarch_cg/cp_id_instr_category/1'
ARRIVAL = (Condition('last_pc', 0x100084),)
PREPARE = dict(target=MUL, cycles=64, reset=True,
               words=[[0x100080, 0x00100093], [0x100084, 0x0000006f]])
SUFFIX = dict(target=MUL, cycles=64, reset=False,
              words=[[0x100084, 0x021081b3], [0x100088, 0xffdff06f]])


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    preparation_start = time.monotonic()
    backend = IbexBatchBackend(output / 'rtl')
    prefixes = PrefixStore(output / 'prefixes')
    preparation_seconds = time.monotonic() - preparation_start
    ledger = BudgetLedger(output / 'replay_costs.jsonl')
    ledger.preparation(preparation_seconds)
    wrong_probe = backend.execute([PREPARE], observers=[dict(node='anything', hierarchy='tb.dut.anything', width=1, phase='post_edge')])
    ledger.charge_execution(wrong_probe)
    assert not wrong_probe.valid and wrong_probe.cycles == 0 and wrong_probe.error == 'unsupported_observer_binding'
    prepared = backend.execute([PREPARE])
    ledger.charge_execution(prepared)
    assert prepared.valid and MUL not in prepared.monitor_hits and ALU in prepared.monitor_hits
    assert all(c.holds(prepared.state) for c in ARRIVAL), prepared.state
    prefix_id = prefixes.store(prepared, ARRIVAL, MUL)
    assert prefixes.get(prefix_id)['target_hit'] is False, 'A verified partial milestone can be stored despite target failure'
    # Open the persistent store again and use a fresh backend/process.
    prefixes.close()
    prefixes = PrefixStore(output / 'prefixes')
    second_backend = IbexBatchBackend(output / 'rtl')
    replayed = prefixes.replay(prefix_id, second_backend, [SUFFIX])
    ledger.charge_execution(replayed)
    assert replayed.valid and replayed.prefix_verified and MUL in replayed.monitor_hits
    assert replayed.replayed_cycles == prepared.cycles
    assert len(replayed.actions) == 2
    assert any(row['signals'].get('rvfi_valid') == 1 and row['signals'].get('rvfi_instruction') == 0x021081b3
               and row['signals'].get('rvfi_rd_wdata') == 1 for row in replayed.trace)
    wrong_environment = IbexBatchBackend(output / 'rtl')
    wrong_environment.environment = replace(wrong_environment.environment, seed=123)
    rejected = prefixes.replay(prefix_id, wrong_environment, [SUFFIX])
    ledger.charge_execution(rejected)
    assert not rejected.valid and rejected.cycles == 0 and rejected.error == 'prefix_environment_mismatch'
    # Fault injection tests the backend's arrival gate; the durable record is untouched.
    wrong_arrival = dict(prefixes.get(prefix_id), arrival=[dict(signal='last_pc', value=0xdeadbeec, offset=0, op='eq')])
    stopped = backend.execute([SUFFIX], prefix=wrong_arrival)
    ledger.charge_execution(stopped)
    assert not stopped.valid and stopped.error == 'prefix_arrival_mismatch'
    assert len(stopped.actions) == 1 and stopped.cycles == prepared.cycles and not stopped.monitor_hits
    try:
        prefixes.store(prepared, ARRIVAL, MUL, complete_preparation=False)
        raise AssertionError('Incomplete preparation accepted')
    except ValueError:
        pass

    class DemonstrationGenerator:
        """Deterministic integration fixture, explicitly not an LLM performance experiment."""
        def generate(self, context):
            assert context['knowledge'] and context['goal']
            if context['phase'] == 'Initial':
                return Generation([PREPARE])
            assert context['experience'] and context['evidence'] and context['prefixes']
            return Generation([SUFFIX], prefix_id=context['prefixes'][0]['id'])

    integration_preparation_start = time.monotonic()
    knowledge = KnowledgeBase(output / 'integration_knowledge.sqlite')
    document = knowledge.ingest(FCOV / 'core_ibex_fcov_if.sv', 'coverage', 'pinned-Ibex')
    for target in (MUL, ALU):
        knowledge.link(document, 'bin', target)
    experiences = ExperienceStore(output / 'experience.sqlite')
    integration_prefixes = PrefixStore(output / 'integration_prefixes')
    integration_preparation_seconds = time.monotonic() - integration_preparation_start
    integration_costs = BudgetLedger(output / 'integration_costs.jsonl')
    integration_costs.preparation(integration_preparation_seconds)
    goals = {MUL: Goal(MUL, ((Condition('rvfi_instruction', 0x021081b3), Condition('rvfi_valid', 1)),), (Condition('reset_n', 1),)),
             ALU: Goal(ALU, ((Condition('rvfi_instruction', 0x00100093), Condition('rvfi_valid', 1)),), (Condition('reset_n', 1),))}
    integrated = run_two_pass([MUL, ALU], DemonstrationGenerator(), backend, EvidenceJudge(goals),
                              experiences, integration_prefixes, integration_costs, goals=goals,
                              knowledge=knowledge, arrival_conditions={MUL: ARRIVAL})
    assert integrated['remaining'] == []
    assert [row['phase'] for row in integrated['history']] == ['Initial', 'Initial', 'Refine']
    assert [row['depth'] for row in integrated['history']] == [0, 1, 2]
    assert integrated['history'][-1]['prefix_used']
    saved = experiences.find(MUL)
    assert any(r['success'] for r in saved) and any(not r['success'] for r in saved)
    assert integrated['costs']['model_calls'] == 0 and integrated['costs']['replay_cycles'] == prepared.cycles
    (output / 'integration.json').write_text(json.dumps(integrated, indent=2))
    recounts = []
    for folder in sorted((output / 'rtl').iterdir()):
        recounts.append(dict(directory=folder.name, **audit(folder)))
    assert len(recounts) == 6 and all(r['passed'] for r in recounts)
    receipt = dict(passed=True, real_full_ibex_processes=len(recounts), prefix_id=prefix_id,
                   partial_milestone_saved=True, fresh_process_replay=True, suffix_mul_result=1,
                   environment_mismatch_rejected=True, wrong_arrival_stopped_before_suffix=True,
                   incomplete_preparation_rejected=True, unsupported_observer_binding_rejected=True, initial_refine_integration=True,
                   successful_and_failed_experience_saved=True, measured_replay_costs=ledger.snapshot(),
                   integration_costs=integrated['costs'], recounts=recounts, model_calls=0,
                   scope='deterministic RTL integration fixtures, not newly generated model stimuli')
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2))
    for item in (prefixes, integration_prefixes, experiences, knowledge):
        item.close()
    print(json.dumps({k: v for k, v in receipt.items() if k != 'recounts'}, indent=2), flush=True)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
