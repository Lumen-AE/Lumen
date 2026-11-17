"""Validate the frozen experiment contract."""
import hashlib
import json
from pathlib import Path
from lumen.paths import PROFILES, catalog_path


def load_config(path=None):
    config = json.loads(Path(path or PROFILES / 'experiment.json').read_text())
    path_to_catalog = catalog_path(config['catalog'])
    assert hashlib.sha256(path_to_catalog.read_bytes()).hexdigest() == config['catalog_sha256'], 'frozen catalog changed'
    catalog = json.loads(path_to_catalog.read_text())
    assert config['denominator'] == len(catalog['targets']) == catalog['total']
    assert config['failure_criterion'] == 'assigned_target_not_hit'
    assert config['consecutive_target_misses'] == 2
    assert config['scoring'] == 'cumulative_distinct_bin_union'
    return config, catalog


