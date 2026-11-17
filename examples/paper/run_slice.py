"""Compile the extracted cone and generated read-only probes in real Verilator."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from lumen.design.graph import DesignGraph
from lumen.reasoning.temporal import Goal
from lumen.observation.comparison import compare, compress, expand, window
from lumen.observation.selection import Probe, ProbeRegistry


def run(reasoning, output):
    reasoning, output = Path(reasoning), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    graph = DesignGraph.load(reasoning / 'frontend/graph.json')
    plan = json.loads((reasoning / 'temporal_plan.json').read_text())
    goal = Goal.from_dict(plan['goal'])
    candidates = json.loads((reasoning / 'observers.json').read_text())['candidates']
    registry = ProbeRegistry(graph, [Probe(**{k: v for k, v in p.items() if k != 'bus_offset'}) for p in candidates])
    source = output / 'debug_slice.sv'
    source.write_bytes((reasoning / 'source/debug_slice.sv').read_bytes())
    inputs = graph.module['ports']
    names = [name for name, item in inputs.items() if item['direction'] == 'input']
    declarations = '\n'.join(f'logic [{len(inputs[name]["bits"]) - 1}:0] {name};' for name in names)
    connections = ', '.join(f'.{name}({name})' for name in names)
    watched = [item['node'] for item in candidates]
    fmt = '{"cycle":%0d,"probe_bus":"%h","signals":{' + ','.join('"' + name + '":%0d' for name in watched) + '}}'
    display = '$display(' + json.dumps(fmt) + ', step, lumen_diagnostic_bus, ' + ', '.join('dut.' + n for n in watched) + ');'
    defaults = '\n'.join(name + ' = 0;' for name in names if name not in ('clk_i', 'rst_ni'))
    body = f'''module tb;
{declarations}
integer failure, step;
debug_slice dut({connections});
{(reasoning / 'candidate_probes.svh').read_text()}
initial begin
  failure=0;
  if ($value$plusargs("failure=%d", failure)) begin end
  clk_i=0; rst_ni=1; #1; rst_ni=0;
  for (step=0; step<7; step=step+1) begin
    clk_i=0;
    {defaults}
    decoded_category=1;
    rst_ni=(step!=0);
    if (step==1) begin if_instr_valid=1; id_in_ready_i=1; end
    if (step==2) begin stall_mem=1; flush_id=(failure==0); end
    if (step==4 || step==5) begin debug_entry_if=1; end
    #5;
    {display}
    clk_i=1; #5;
  end
  $finish;
end
endmodule
'''
    (output / 'tb.sv').write_text(body)
    tool = shutil.which('verilator')
    if not tool:
        raise RuntimeError('Verilator is required')
    result = subprocess.run([tool, '--binary', '--timing', '--top-module', 'tb', '--Mdir', 'build', '-o', 'simulate',
                             '-Wno-fatal', 'debug_slice.sv', 'tb.sv'], cwd=output, capture_output=True, text=True, timeout=240)
    (output / 'build.log').write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError('Slice build failed: ' + str(output / 'build.log'))
    summaries = []
    for failure in (0, 1):
        name = 'failure' if failure else 'success'
        result = subprocess.run([str(output / 'build/simulate'), '+failure=' + str(failure)], cwd=output, capture_output=True, text=True, check=True)
        (output / (name + '.log')).write_text(result.stdout + result.stderr)
        trace = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{"cycle":')]
        assert len(trace) == 7
        for row in trace:
            bus = int(row.pop('probe_bus'), 16)
            for candidate in candidates:
                measured = (bus >> candidate['bus_offset']) & ((1 << candidate['width']) - 1)
                assert measured == row['signals'][candidate['node']], candidate
            row.update(phase='pre_edge_effective', core_edge=True, reset_active=not row['signals']['rst_ni'],
                       events=['unstall'] if row['signals']['instr_unstalled'] else [])
        hits = {goal.bin_id} if any(row['signals']['monitor_hit'] for row in trace) else set()
        milestones = [c for m in plan['milestones'] for c in m['conditions']]
        evidence = compare(goal, trace, hits, milestones, anchor_cycle=4)
        assert evidence['monitor_hit'] == evidence['predicate_match'] == (not failure)
        if failure:
            assert any(c['signal'] == 'flush_id' and c['cycle'] == 2 and c['matched'] is False for c in evidence['checks'])
            assert evidence['revision'] == 'adjust_order_duration_or_spacing'
            expanded = []
            for depth in range(3):
                selection = registry.select(goal, depth)
                partial = [dict(row, signals=registry.project(row, selection)['values']) for row in trace]
                assessed = compare(goal, partial, hits, milestones, anchor_cycle=4)
                expanded.append(dict(selection=selection, evidence=assessed))
            assert expanded[0]['evidence']['unexplained']
            assert not expanded[-1]['evidence']['unexplained']
            (output / 'observation_expansion.json').write_text(json.dumps(expanded, indent=2))
        compressed = compress(trace)
        assert expand(compressed) == trace
        assert all(part['count'] == 1 for part in compressed if part['protected'])
        evidence['window'] = compress(window(trace, 2 if failure else 4))
        (output / (name + '_trace.json')).write_text(json.dumps(trace, indent=2))
        (output / (name + '_evidence.json')).write_text(json.dumps(evidence, indent=2))
        summaries.append(dict(case=name, passed=True, monitor_hit=bool(hits), predicate_match=evidence['predicate_match'],
                              revision=evidence['revision'], samples=len(trace), generated_probe_values_verified=True))
    receipt = dict(passed=True, cases=summaries, lossless_window_roundtrip=True, real_verilator=True, graph_expansion_resolved_missing_conditions=True,
                   scope='extracted actual source cone; externally declared cutpoint stimuli')
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2), flush=True)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reasoning', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.reasoning, args.output)
