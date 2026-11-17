"""Ibex instruction and data bus response model."""

class Memory:
    def __init__(self, dut, name):
        self.dut, self.name = dut, name
        self.bytes = {}
        self.latency = 2
        self.errors = {}
        self.pending = []
        self.transaction_log = []

    def put_word(self, addr, word, be=15):
        for i in range(4):
            if be & (1 << i): self.bytes[addr+i] = (word >> (8*i)) & 255

    def word(self, addr):
        # Preserve upstream MemAgent's unmapped-memory word, rather than supplying programs.
        default = 0xC0001073
        return sum(self.bytes.get(addr+i, (default >> (8*i)) & 255) << (8*i) for i in range(4))

    def drive(self, cycle):
        def setv(suffix, value): getattr(self.dut, self.name+'_'+suffix).value = value
        setv('gnt_i', 1)
        setv('rvalid_i', 0); setv('err_i', 0); setv('rdata_i', 0)
        if self.pending and self.pending[0]['due'] <= cycle:
            item = self.pending.pop(0)
            setv('rvalid_i', 1); setv('err_i', item['error']); setv('rdata_i', item['word'])

    def request(self, cycle):
        def get(suffix): return int(getattr(self.dut, self.name+'_'+suffix).value)
        if not (get('req_o') and get('gnt_i')): return
        addr = get('addr_o') & ~3
        fail = int(self.errors.get(addr, 0) > 0)
        if fail: self.errors[addr] -= 1
        is_write = self.name == 'data' and get('we_o')
        if is_write and not fail:
            # Includes zero writes and byte enables, unlike the original MemAgent.
            self.put_word(addr, get('wdata_o'), get('be_o'))
        self.pending.append(dict(due=cycle+self.latency, error=fail, word=self.word(addr)))
        self.transaction_log.append(dict(cycle=cycle, address=addr, error=fail,
                                         write=bool(is_write), latency=self.latency))


