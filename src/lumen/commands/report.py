"""Report baseline and subsequent evidence rescue as cumulative union / 3832."""
import argparse
import json
from pathlib import Path

from lumen.paths import ROOT
def read(path):return json.loads(path.read_text(encoding='utf-8'))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--evidence',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    base=read(a.baseline/'trial_summary.json')
    b=set(read(a.baseline/'covered_bins.json'))
    assert base['finished'] and base['denominator_valid'] and base['total']==3832
    assert base['submitted_model_responses']>0
    if a.evidence:
        ev=read(a.evidence/'trial_summary.json')
        e=set(read(a.evidence/'stage_covered_bins.json'))
        final=set(read(a.evidence/'covered_bins.json'))
        assert ev['finished'] and ev['denominator_valid'] and ev['total']==3832
        assert ev['initial_hit']==len(b) and ev['catalog_sha256']==base['catalog_sha256']
        assert ev['model']==base['model'], 'keep the same model settings for both stages'
        assert final==b|e
    else:
        assert len(b)==3832, 'evidence stage is still required for remaining bins'
        ev={};e=set();final=b
    assert len(b)==base['hit'] and len(final)<=3832
    report=dict(completed=True,design='sequential_baseline_then_evidence_rescue',denominator=3832,
                baseline_hit=len(b),baseline_percent=100*len(b)/3832,
                evidence_additional_hit=len(e-b),final_union_hit=len(final),
                final_percent=100*len(final)/3832,remaining=3832-len(final),
                baseline_model_responses=base['submitted_model_responses'],
                evidence_model_responses=ev.get('submitted_model_responses',0),model=base['model'],
                baseline_stop_reason=base['stop_reason'],evidence_stop_reason=ev.get('stop_reason'),
                independent_AB_comparison=False,llm_api_used=base['model']['provider']=='openai_compatible',cli_model_inference_used=False)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'final_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    transport = 'Model API' if report['llm_api_used'] else 'Desktop dialogue relay'
    md=f'''# Lumen experiment report

Model: {base['model']['model_id']}. Reasoning setting: {base['model']['reasoning_effort']}. Transport: {transport}.

| Feedback | Covered bins | Coverage |
|---|---:|---:|
| baseline | {len(b)} / 3832 | {100*len(b)/3832:.2f}% |
| evidence additions | {len(e-b)} | +{100*len(e-b)/3832:.2f} percentage points |
| cumulative union | {len(final)} / 3832 | {100*len(final)/3832:.2f}% |

Remaining bins: {3832-len(final)}. Submitted responses: {base['submitted_model_responses']} baseline, {ev.get('submitted_model_responses',0)} evidence.

Evidence continues from the completed baseline coverage set. The report describes cumulative coverage, rather than an independent A/B comparison.
'''
    (a.output/'FINAL_REPORT.md').write_text(md,encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
