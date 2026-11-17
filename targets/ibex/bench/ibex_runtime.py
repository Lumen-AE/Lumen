"""LUMEN runtime; preserves the existing pre-edge sampling/clock discipline."""
import json,os
from pathlib import Path
from ibex_clock import Runtime
from ibex_memory import Memory
from lumen.engine.actions import ALLOWED_PINS
from lumen.engine import artifacts


class RetirementHistory:
    """Last retired instruction only; no legacy coverage predicates or bins."""
    def __init__(self): self.last=None
    def sample(self,valid,word):
        if valid: self.last=word
    def report(self): return dict(kind='retirement_history_only',counts={})


class LumenRuntime(Runtime):
    def __init__(self,dut,arm='baseline'):
        # Do not construct HC89/ExtendedCoverage/LegacyCoverage. Only the
        # official frozen subset is used, including auxiliary reports.
        self.dut,self.arm,self.trace_limit=dut,arm,64
        self.imem=Memory(dut,'instr'); self.dmem=Memory(dut,'data')
        catalog = os.environ.get('LUMEN_CATALOG', 'official_current')
        if catalog != 'official_current':
            raise ValueError('Only the frozen official_current catalog is supported')
        from lumen.coverage.scorer import FullCoverage
        self.coverage = FullCoverage(catalog)
        self.suite = self.coverage.catalog_name
        self.legacy=RetirementHistory()  # Attribute reused for retirement history.
        self.legacy_records={}
        self.termination=None
        self.cycle=0;self.trace=[];self.audit=[];self.rounds=0
        self.last_pc=self.last_instruction=None
        for pin in ALLOWED_PINS: getattr(dut,pin+'_i').value=0
        dut.rst_ni.value=0;dut.clk_i.value=0

    async def action(self,raw,max_cycles=4096):
        # The full scorer supplies declaration-specific source-derived evidence.
        # Avoid the old fixed manual observer map in the inherited implementation.
        arm = self.arm
        start = len(self.trace)
        if hasattr(self.coverage, 'evidence'):
            self.arm = 'baseline'
        try:
            result=await super().action(raw,max_cycles)
        finally:
            self.arm = arm
        if arm == 'evidence' and hasattr(self.coverage, 'evidence') and raw.get('target') in self.coverage.records:
            result['evidence'] = self.coverage.evidence(raw['target'], self.trace[start:], self.trace_limit)
        result.pop('legacy_196',None)
        return result

    async def reject(self,raw,error,cycles):
        result=await super().reject(raw,error,cycles)
        result.pop('legacy_196',None)
        return result

    def save_audit(self,destination):
        path=Path(destination);path.mkdir(parents=True,exist_ok=True)
        report=dict(coverage=self.primary_report(),primary=self.primary_report(),
            cycles=self.cycle,rounds=self.rounds,arm=self.arm,suite=self.suite,
            profile=os.environ.get('LUMEN_PROFILE'),catalog=self.coverage.catalog_name,termination=self.termination,
            scope='official original coverage definitions only; no authored/legacy additions')
        artifacts.write_json(path/'report.json', report)
        if getattr(self, 'stream_destination', None) is not None:
            assert path == self.stream_destination
            self.flush_stream()
        else:
            artifacts.write_text(path/'internal_trace.jsonl', ''.join(json.dumps(row)+'\n' for row in self.trace))
            artifacts.write_text(path/'actions_and_feedback.jsonl', ''.join(json.dumps(row)+'\n' for row in self.audit))
        artifacts.write_json(path/'first_hit_witnesses.json', self.coverage.witness)

    def enable_streaming(self, destination):
        """Bound live RAM to one attempt, while preserving every raw RTL sample."""
        self.stream_destination = Path(destination)
        self.stream_destination.mkdir(parents=True, exist_ok=True)
        for name in ('internal_trace.jsonl', 'actions_and_feedback.jsonl'):
            artifacts.write_text(self.stream_destination / name, '')

    def flush_stream(self):
        if getattr(self, 'stream_destination', None) is None:
            return
        with artifacts.append_text(self.stream_destination / 'internal_trace.jsonl') as stream:
            for row in self.trace:
                stream.write(json.dumps(row) + '\n')
        with artifacts.append_text(self.stream_destination / 'actions_and_feedback.jsonl') as stream:
            for row in self.audit:
                item = dict(row)
                feedback = dict(item['feedback'])
                feedback['coverage'] = {k: v for k, v in feedback['coverage'].items() if k not in ('counts', 'missing')}
                item['feedback'] = feedback
                stream.write(json.dumps(item) + '\n')
        self.trace.clear()
        self.audit.clear()

    def snapshot(self):
        s = super().snapshot()
        s['official_bus'] = hex(int(self.dut.lumen_official_bus_o.value))
        for name in ('profile','mpp','mprv','priv_lsu','nmi','irq_pending','debug_req',
                     'ls_error','ls_pmp','ls_first','ls_second','ls_mis_pmp_2',
                     'ls_data_pmp','if_compressed','wb_valid','wb_load','wb_store',
                     'pmp_err','match_i','match_i2','match_d','current_priv_err',
                     'mcause','mepc','mtval','pmp_cfg'):
            key = name+'_fcov' if name in ('irq_pending','debug_req') else name
            s[key] = int(getattr(self.dut,'lumen_'+name+'_o').value)
        for name in ('trap','rd_addr','rd_wdata','mem_addr','mem_rmask','mem_wmask',
                     'mem_rdata','mem_wdata','mode'):
            s['rvfi_'+name] = int(getattr(self.dut.u_top,'rvfi_'+name).value)
        return s
