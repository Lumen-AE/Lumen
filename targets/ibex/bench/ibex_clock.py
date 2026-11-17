"""Cocotb runtime shared by both arms. No assembler/compiler/encoder/tool executor."""
from pathlib import Path
import json
import os
from cocotb.triggers import Timer, ReadOnly
from lumen.observation.samples import FSM, FLAGS, enrich
from lumen.engine.actions import validate, ALLOWED_PINS


class Runtime:
    def snapshot(self):
        d = self.dut
        flags = int(d.lumen_flags_o.value)
        s = {name:(flags >> i)&1 for i,name in enumerate(FLAGS)}
        for key in ('instruction','pc','mie','lsu_state','data_error','data_response'):
            s[key] = int(getattr(d, 'lumen_'+key+'_o').value)
        s['fsm'] = FSM[int(d.lumen_fsm_o.value)]
        s['next_fsm'] = FSM[int(d.lumen_next_fsm_o.value)]
        s['irq_bits'] = int(d.lumen_irqs_o.value)
        s['privilege'] = {0:'U', 3:'M'}.get(int(d.lumen_privilege_o.value), 'INVALID')
        s['reset_n'] = int(d.rst_ni.value)
        s['first_error'] = self.coverage.first_error
        s['second_pending'] = self.coverage.second_pending
        s['debug_request'] = int(d.debug_req_i.value)
        s['data_request'] = int(d.data_req_o.value) and int(d.data_gnt_i.value)
        s['data_write'] = int(d.data_we_o.value)
        s['rvfi_valid'] = int(d.u_top.rvfi_valid.value)
        s['rvfi_pc'] = int(d.u_top.rvfi_pc_rdata.value)
        s['rvfi_instruction'] = int(d.u_top.rvfi_insn.value)
        s['previous_retired_instruction'] = self.legacy.last
        return s

    def primary_report(self):
        return self.coverage.report()

    async def tick(self):
        # Deliberately manual clock: stable pre-edge sample avoids cocotb/NBA races.
        d = self.dut; d.clk_i.value = 0
        self.imem.drive(self.cycle); self.dmem.drive(self.cycle)
        await Timer(5, units='ns'); await ReadOnly()
        sample = self.snapshot()
        rvfi = (int(d.u_top.rvfi_valid.value), int(d.u_top.rvfi_insn.value), int(d.u_top.rvfi_pc_rdata.value))
        accepted = int(d.rst_ni.value)
        if accepted:
            self.imem.request(self.cycle); self.dmem.request(self.cycle)
        await Timer(1, units='ps')
        d.clk_i.value = 1
        await Timer(1, units='ps'); await ReadOnly()
        sample['core_edge'] = int(d.lumen_core_clk_o.value)
        new = self.coverage.sample(sample, self.cycle)
        if sample['core_edge'] and accepted:
            self.legacy.sample(rvfi[0], rvfi[1])
            if rvfi[0]: self.last_pc, self.last_instruction = rvfi[2], rvfi[1]
        entry = dict(cycle=self.cycle, **enrich(sample), new_bins=new)
        self.trace.append(entry)
        await Timer(4998, units='ps')
        self.cycle += 1

    async def reset(self):
        self.dut.rst_ni.value = 0
        self.legacy.last = None
        for pin in ALLOWED_PINS: getattr(self.dut, pin+'_i').value = 0
        self.imem.pending.clear(); self.dmem.pending.clear()
        # Only uncommitted transactions are flushed; memories and accumulated coverage persist.
        for _ in range(4): await self.tick()
        self.dut.rst_ni.value = 1

    async def action(self, raw, max_cycles=4096):
        action = validate(raw, max_cycles=max_cycles)
        records = self.coverage.records
        if action['target'] is not None and action['target'] not in records:
            raise ValueError('unknown target for the selected suite')
        start = len(self.trace)
        for name, mem in (('words', self.imem), ('data_words', self.dmem)):
            for addr, word in action[name]: mem.put_word(addr, word)
        for prefix, mem in (('instruction', self.imem), ('data', self.dmem)):
            if prefix+'_latency' in action['memory']: mem.latency = action['memory'][prefix+'_latency']
            if prefix+'_errors' in action['memory']: mem.errors = dict(action['memory'][prefix+'_errors'])
        if action['reset']: await self.reset()
        before = set(self.primary_report()['missing'])
        events = {}
        for ev in action['events']: events.setdefault(ev['at'], []).append(ev)
        # A model-requested reset is charged to the SAME per-call cycle budget.
        active_cycles = action['cycles'] - (4 if action['reset'] else 0)
        for i in range(active_cycles):
            for ev in events.get(i, []): getattr(self.dut, ev['pin']+'_i').value = ev['value']
            await self.tick()
        self.rounds += 1
        report = self.primary_report()
        feedback = dict(round=self.rounds, cycle=self.cycle, last_pc=self.last_pc,
                        last_instruction=self.last_instruction, coverage=report,
                        new_bins=sorted(before - set(report['missing'])))
        self.audit.append(dict(round=self.rounds, action=action, feedback=feedback))
        return feedback

    async def reject(self, raw, error, cycles):
        for _ in range(cycles): await self.tick()
        self.rounds += 1
        reply = dict(error=str(error), round=self.rounds, cycle=self.cycle,
                     last_pc=self.last_pc, last_instruction=self.last_instruction,
                     coverage=self.primary_report())
        self.audit.append(dict(round=self.rounds, action=raw, rejected=True, feedback=reply))
        return reply
