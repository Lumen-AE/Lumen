"""Diagnostic sample labels; official scoring is in lumen.coverage.scorer."""
FSM = ('RESET', 'BOOT_SET', 'WAIT_SLEEP', 'SLEEP', 'FIRST_FETCH', 'DECODE',
       'FLUSH', 'IRQ_TAKEN', 'DBG_TAKEN_IF', 'DBG_TAKEN_ID')
FLAGS = (
    'valid', 'fetch_error', 'illegal_c', 'illegal_dec', 'illegal_csr',
    'illegal_csr_priv', 'illegal_csr_dbg', 'illegal_out', 'illegal_dret',
    'illegal_umode', 'ebreakm', 'ebreaku', 'stall_mem', 'stall_ld',
    'stall_muldiv', 'stall_branch', 'stall_jump', 'debug_mode', 'irq_pending',
    'all_debug_req', 'debug_wakeup', 'interrupt_taken', 'debug_entry_if',
    'debug_entry_id', 'pipe_flush', 'step_taken', 'do_step', 'mret_dec',
    'wfi_dec', 'csr_read_only', 'csr_write', 'csr_invalid',
)

def category(s):
    """Official category precedence, including invalid/privileged instructions."""
    w = s['instruction']; op = w & 127; f3 = (w >> 12) & 7; f7 = w >> 25
    c = {0x37:'ALU', 0x17:'ALU', 0x6f:'Jump', 0x67:'Jump', 0x63:'Branch',
         0x03:'Load', 0x23:'Store', 0x13:'ALU'}.get(op, 'Other')
    if op == 0x33:
        if (((w >> 26) & 1) and ((w >> 12) & 3) == 1) or f7 in (0, 0x20, 0x30, 0x34, 0x14, 0x10, 5, 4, 0x24):
            c = 'ALU'
        elif f7 == 1:
            c = 'Div' if f3 & 4 else 'Mul'
    elif op == 0x73:
        if f3:
            c = 'CSRAccess'
        else:
            c = {0:'ECall', 1:'EBreakExc', 0x302:'MRet', 0x7b2:'DRet', 0x105:'WFI'}.get(w >> 20, 'Other')
            if c == 'EBreakExc' and ((s['ebreakm'] and s['privilege'] == 'M') or
                                     (s['ebreaku'] and s['privilege'] == 'U')):
                c = 'EBreakDbg'
    elif op == 0x0f:
        c = {0:'Fence', 1:'FenceI'}.get(f3, 'Other')
    if not s['valid']: return 'None'
    if s['fetch_error']: return 'FetchError'
    if s['illegal_c']: return 'CompressedIllegal'
    if s['illegal_dec']: return 'UncompressedIllegal'
    if s['illegal_csr']:
        return 'PrivIllegal' if s['illegal_csr_priv'] or s['illegal_csr_dbg'] else 'CSRIllegal'
    if s['illegal_out']:
        return 'PrivIllegal' if s['illegal_dret'] or s['illegal_umode'] else 'OtherIllegal'
    return c


def enrich(s):
    s = dict(s)
    s['category'] = category(s)
    s['stall'] = ('Instr' if s['stall_muldiv'] or s['stall_branch'] or s['stall_jump']
                  else 'LdHz' if s['stall_ld'] else 'Mem' if s['stall_mem'] else 'None') if s['valid'] else 'None'
    return s


