"""Select baseline-missing targets without changing the 3832-bin denominator."""
import argparse
import hashlib
import json
from pathlib import Path

from lumen.paths import ROOT
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    summary=read(a.baseline/'trial_summary.json')
    covered=read(a.baseline/'covered_bins.json')
    catalog=ROOT/'targets/ibex/coverage/counted.json'
    ids={r['id'] for r in read(catalog)['targets']}
    assert len(ids)==3832 and summary['total']==3832
    assert summary['finished'] and summary['denominator_valid'], 'baseline has not completed validly'
    assert summary['catalog_sha256']==sha(catalog)
    assert summary['submitted_model_responses']>0, 'calibration is not a formal baseline'
    assert summary['model']['provider'] in ('codex_desktop_dialogue', 'openai_compatible')
    assert len(set(covered))==summary['hit'] and set(covered)<=ids
    seed=dict(schema=1,baseline_completed=True,catalog_sha256=sha(catalog),denominator=3832,
              baseline_summary_sha256=sha(a.baseline/'trial_summary.json'),
              baseline_covered_ids_sha256=sha(a.baseline/'covered_bins.json'),
              baseline_responses=summary['submitted_model_responses'],covered_ids=covered,
              remaining_ids=[r['id'] for r in read(catalog)['targets'] if r['id'] not in set(covered)],
              baseline_model=summary['model'],baseline_directory=str(a.baseline.resolve()))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(seed,indent=2),encoding='utf-8')
    print(json.dumps(dict(baseline_hit=len(covered),remaining=len(ids)-len(covered),total=3832,
                          maximum_evidence_actions=2*(len(ids)-len(covered)),seed=str(a.output))))

if __name__=='__main__':main()
