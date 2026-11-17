"""Decode the fixed read-only probe bus."""
import json
from functools import lru_cache
from lumen.paths import COVERAGE


@lru_cache(maxsize=1)
def observer_map():
    return json.loads((COVERAGE / 'probes.json').read_text())


def transactions(bus):
    """Decode the stable pre-edge probe bus, including every iff answer."""
    result = {}
    value = int(bus, 16) if isinstance(bus, str) else bus
    for probe in observer_map()['probes']:
        key = (probe['group'], probe['instance'])
        item = result.setdefault(key, dict(values={}, gates={}))
        field = 'values' if probe['kind'] == 'value' else 'gates'
        item[field][probe['key']] = (value >> (32 * probe['slot'])) & 0xffffffff
    return result


