"""Checkout-local resource locations; independent of cwd and legacy trees."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IBEX = ROOT / 'targets' / 'ibex'
COVERAGE = IBEX / 'coverage'
REFERENCE = COVERAGE / 'reference'
FCOV = REFERENCE / 'ibex/dv/uvm/core_ibex/fcov'
PUBLIC = IBEX / 'public'
PROFILES = ROOT / 'profiles'
WORKFLOWS = ROOT / 'workflows'

def catalog_path(name='official_current'):
    if name != 'official_current':
        raise ValueError('Only the frozen official_current catalog is supported')
    return COVERAGE / 'counted.json'

def public_files(arm):
    if arm not in ('base', 'evidence'):
        raise ValueError('Unknown experiment arm')
    return [('SUBJECT.md', WORKFLOWS / (arm + '.md')),
            ('context.md', PUBLIC / 'context.md'),
            ('protocol.json', PUBLIC / 'protocol.json'),
            ('coverage.sv.txt', PUBLIC / 'coverage.sv.txt'),
            ('rtl.txt', PUBLIC / 'rtl.txt')]
