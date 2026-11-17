"""Source-dependent projection of actual probe samples."""
from .probes import transactions


def select_evidence(record, definition, hit, target, rows, limit=64):
    group, instance = record['group'], record.get('instance')
    names = set(definition.get('dimensions', [definition['name']]))
    gate_ids = {record['declaration']} | {group + '/' + name for name in names}
    result = []
    for row in rows[-limit:]:
        if not row.get('core_edge') or not row.get('reset_n'):
            continue
        item = transactions(row['official_bus'])[(group, instance)]
        result.append(dict(cycle=row['cycle'], pc=row['pc'], instruction=row['instruction'],
                           values={k: v for k, v in item['values'].items() if k in names},
                           gates={k: v for k, v in item['gates'].items() if k in gate_ids or k.startswith(record['declaration'] + '/')}))
    return dict(target=target, selector='official_source_probe_dependencies', trace=result,
                hit=bool(hit))

