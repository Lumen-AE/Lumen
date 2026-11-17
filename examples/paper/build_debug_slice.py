"""Extract the paper's register/control cone from pinned Ibex source.

This is a source-mapped slice with explicit cutpoints, not a full CPU model.
The word graph is subsequently produced by Yosys, never authored by hand.
"""
import hashlib
import json
from pathlib import Path
import re
from lumen.paths import IBEX, FCOV


def extract(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    rtl = IBEX / 'rtl/lowrisc_ibex_ibex_core_0.1/rtl'
    files = {name: (rtl / name) for name in ('ibex_if_stage.sv', 'ibex_id_stage.sv', 'ibex_controller.sv')}
    files['core_ibex_fcov_if.sv'] = FCOV / 'core_ibex_fcov_if.sv'
    texts = {name: path.read_text(encoding='utf-8') for name, path in files.items()}
    provenance = []
    def grab(file, pattern):
        match = re.search(pattern, texts[file], re.S)
        if not match:
            raise ValueError('Pinned source no longer matches the extraction contract: ' + file)
        snippet = match.group(0)
        provenance.append(dict(file=file, source_sha256=hashlib.sha256(files[file].read_bytes()).hexdigest(),
                               line_start=texts[file].count('\n', 0, match.start()) + 1,
                               line_end=texts[file].count('\n', 0, match.end()) + 1,
                               snippet_sha256=hashlib.sha256(snippet.encode()).hexdigest()))
        return snippet
    enums = grab('core_ibex_fcov_if.sv', r'typedef enum \{.*?\} instr_category_e;') + '\n' + grab('core_ibex_fcov_if.sv', r'typedef enum \{\s*IdStallTypeNone.*?\} id_stall_type_e;')
    updates = grab('ibex_if_stage.sv', r'assign instr_valid_id_d = .*?\n  end\n')
    stall = grab('ibex_id_stage.sv', r'assign stall_id = .*?;')
    stall += '\n' + grab('ibex_controller.sv', r'assign stall = .*?;').replace('stall_id_i', 'stall_id')
    clear = grab('ibex_controller.sv', r'assign instr_valid_clear_o = .*?;').replace('instr_valid_clear_o', 'instr_valid_clear_i')
    category = grab('core_ibex_fcov_if.sv', r'// Set `id_stall_type`.*?\n  end\n')
    category = category.replace('id_stage_i.instr_valid_i', 'instr_valid_id_q').replace('id_stage_i.', '')
    history = grab('core_ibex_fcov_if.sv', r'always @\(posedge clk_i or negedge rst_ni\) begin\s*if \(!rst_ni\) begin\s*// First cycle.*?id_stall_type_last_valid;')
    none_branch = grab('core_ibex_fcov_if.sv', r'end else begin\s*id_instr_category = InstrCategoryNone;\s*end')
    source = '''// Derived from pinned lowRISC Ibex files. Copyright lowRISC contributors.
// SPDX-License-Identifier: Apache-2.0
// Explicit cutpoints: decoded category, stall causes, flush/retain, new-fetch controls and Debug entry.
module debug_slice(
 input logic clk_i, rst_ni, if_instr_valid, id_in_ready_i, pc_set_i,
 input logic stall_mem, stall_ld_hz, stall_multdiv, stall_branch, stall_jump, stall_alu,
 input logic stall_wb_i, retain_id, flush_id, debug_entry_if,
 input logic [31:0] decoded_category,
 output logic instr_valid_id_q, instr_valid_id_d, instr_new_id_d, instr_new_id_q,
 output logic instr_valid_clear_i, stall_id, stall,
 output logic [31:0] id_instr_category, id_stall_type, id_stall_type_last, id_instr_category_last,
 output logic id_stall_type_last_valid, instr_unstalled, instr_unstalled_last,
 output logic new_input, monitor_hit
);
''' + enums + '\n' + updates + '\n' + stall + '\n' + clear + '\n' + category + '\n' + history + '''
// Decoding is an explicit cutpoint. Valid decoded instructions never have the None category.
assign id_instr_category = instr_valid_id_q ? decoded_category : InstrCategoryNone;
assign new_input = if_instr_valid & id_in_ready_i & ~pc_set_i;
// Literal finite-bin predicate from the frozen debug_entry_if_instr_cross.
assign monitor_hit = rst_ni && debug_entry_if && instr_unstalled_last &&
                     (id_instr_category_last == InstrCategoryNone);
endmodule
'''
    path = output / 'debug_slice.sv'
    path.write_text(source, encoding='utf-8')
    (output / 'source_map.json').write_text(json.dumps(dict(sources=provenance,
        adaptations=['Hierarchy cutpoints renamed to ports; stall_id connected to its actual OR expression',
                     'Category decoding abstracted before the source None override; require decoded_category != 16',
                     'Debug entering event is a cutpoint, not the external debug request',
                     'DUT and coverage history update equations extracted; no full-core reachability claim']), indent=2))
    return path
