"""Validate literal machine words and external pin schedules. No instruction encoder."""
ALLOWED_PINS = {'irq_software', 'irq_timer', 'irq_external', 'irq_nm', 'irq_fast', 'debug_req'}


def integer(value):
    if isinstance(value, bool): raise ValueError('booleans are not integer words')
    if isinstance(value, int): return value
    if isinstance(value, str): return int(value, 0)
    raise ValueError('expected an integer or hexadecimal string')


def validate(plan, max_cycles=4096, max_words=1024):
    if not isinstance(plan, dict): raise ValueError('action must be a JSON object')
    if set(plan) - {'words','data_words','events','cycles','reset','memory','target'}:
        raise ValueError('unsupported action; only literal memory writes and external pin events are allowed')
    out = dict(cycles=integer(plan.get('cycles', 16)), reset=plan.get('reset', False),
               words=[], data_words=[], events=[], memory=dict(plan.get('memory', {})), target=plan.get('target'))
    if type(out['reset']) is not bool: raise ValueError('reset must be boolean')
    if not 1 <= out['cycles'] <= max_cycles: raise ValueError('cycle budget exceeded')
    if out['reset'] and out['cycles'] < 4: raise ValueError('reset needs four budgeted cycles')
    if out['target'] is not None and not isinstance(out['target'], str): raise ValueError('target must be a string')
    for name in ('words','data_words'):
        if len(plan.get(name, [])) > max_words: raise ValueError('word budget exceeded')
        for pair in plan.get(name, []):
            if not isinstance(pair, list) or len(pair) != 2: raise ValueError('expected [address, literal_word]')
            addr, word = map(integer, pair)
            if addr % 4 or not 0 <= addr <= 0xfffffffc or not 0 <= word <= 0xffffffff:
                raise ValueError('word/address outside aligned 32-bit range')
            out[name].append([addr, word])
    for event in plan.get('events', []):
        if set(event) != {'at','pin','value'} or event['pin'] not in ALLOWED_PINS:
            raise ValueError('external pin event required; internal writes are prohibited')
        at = integer(event['at']); value = integer(event['value'])
        active_cycles = out['cycles'] - (4 if out['reset'] else 0)
        if not 0 <= at < active_cycles or not 0 <= value <= (32767 if event['pin']=='irq_fast' else 1):
            raise ValueError('event outside cycle/pin range')
        out['events'].append(dict(at=at, pin=event['pin'], value=value))
    if set(out['memory']) - {'instruction_latency','data_latency','instruction_errors','data_errors'}:
        raise ValueError('unknown memory setting')
    for key in ('instruction_latency','data_latency'):
        if key in out['memory']:
            n = integer(out['memory'][key])
            if not 1 <= n <= 64: raise ValueError('response latency must be 1..64')
            out['memory'][key] = n
    for key in ('instruction_errors','data_errors'):
        if key in out['memory']:
            # Address -> finite count of failing accepted transactions, NOT hidden instruction encoding.
            out['memory'][key] = {integer(k): integer(v) for k,v in out['memory'][key].items()}
            if any(a % 4 or not 0 <= a <= 0xfffffffc or not 0 <= n <= 64 for a,n in out['memory'][key].items()):
                raise ValueError('invalid error injection rule')
    return out
