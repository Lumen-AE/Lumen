"""Finite-bin elaborator and sampler for all 149 official Ibex declarations.

Input is a normalized observer transaction: values of named coverpoints and
raw cross dimensions, plus explicit gate decisions for declarations with iff.
This is a portable bin model, not a claim of a complete RTL/cocotb binding.
Missing values/gates stay unknown; they are never silently replaced by zero.
"""
from __future__ import annotations
import ast, collections, csv, itertools, json, operator, pathlib, re
from .declarations import balanced, decomment, load_records, split_top
from lumen.paths import REFERENCE, FCOV


def number(text, constants=None):
    text=text.strip().replace('_','') if "'" in text else text.strip()
    m=re.fullmatch(r"(?:\d+)?'[sS]?([bBoOdDhH])([0-9a-fA-F]+)",text)
    if m: return int(m[2],{'b':2,'o':8,'d':10,'h':16}[m[1].lower()])
    if re.fullmatch(r'\d+',text): return int(text)
    return constants[text]

def enums():
    constants={}; types={}
    for path in [REFERENCE/'ibex/rtl/ibex_pkg.sv',FCOV/'core_ibex_fcov_if.sv',FCOV/'core_ibex_pmp_fcov_if.sv']:
        text=decomment(path.read_text())
        for m in re.finditer(r'typedef\s+enum\b[^{}]*\{([^{}]*)\}\s*(\w+)\s*;',text,re.S):
            pairs=[]; current=-1
            for part in split_top(m[1]):
                if not part: continue
                name,*assigned=part.split('=',1)
                name=name.strip()
                if assigned:
                    try: current=number(assigned[0],constants)
                    except (KeyError,ValueError): break
                else: current+=1
                constants[name]=current; pairs.append((name,current))
            else: types[m[2]]=pairs
    return constants,types

CONSTANTS,TYPES=enums()
CONSTANTS.update(IbexMuBiOn=5,IbexMuBiOff=10)

def expand_set(text,wildcard=False):
    text=text.strip()
    if text.startswith('{') and text.endswith('}'): text=text[1:-1].strip()
    if '`' in text:
        macros=decomment((FCOV/'core_ibex_csr_categories.svh').read_text()).replace('\\\n',' ')
        for name in ('IGNORED_CSRS','DEBUG_CSRS'):
            m=re.search(r'`define\s+'+name+r'\s+(.*?)(?=`define|\Z)',macros,re.S)
            if m: text=text.replace('`'+name,m[1].replace('\\','').strip())
    result=[]
    for part in split_top(text):
        part=part.strip()
        if not part: continue
        if part.startswith('['):
            lo,hi=part[1:-1].split(':'); result+=list(range(number(lo,CONSTANTS),number(hi,CONSTANTS)+1))
        elif '?' in part:
            m=re.fullmatch(r"(\d+)'b([01?_]+)",part)
            if not m: raise ValueError(part)
            bits=m[2].replace('_',''); result += [v for v in range(1<<int(m[1])) if all(c=='?' or c==b for c,b in zip(bits,format(v,f'0{len(bits)}b')))]
        else: result.append(number(part,CONSTANTS))
    return sorted(set(result))

def scalar_domain(group,name):
    typed={
        'cp_id_instr_category':'instr_category_e','cp_id_instr_category_last':'instr_category_e',
        'cp_single_step_instr':'instr_category_e','cp_data_ind_timing_instr':'instr_category_e',
        'cp_dummy_instr':'instr_category_e','cp_stall_type_id':'id_stall_type_e',
        'cp_if_stage_state':'if_stage_state_e','cp_id_stage_state':'pipe_stage_state_e',
        'cp_wb_stage_state':'pipe_stage_state_e','wb_stage_state':'pipe_stage_state_e',
        'cp_priv_mode_id':'priv_lvl_e','cp_priv_mode_lsu':'priv_lvl_e',
        'cp_csr_read_only':'csr_num_e','cp_csr_write':'csr_num_e',
        'cp_region_mode':'pmp_cfg_mode_e','cp_region_priv_bits':'pmp_priv_bits_e',
        'pmp_region_priv_bits':'pmp_priv_bits_e','pmp_region_priv_bits_wr':'pmp_priv_bits_e',
        'cs_registers_i.mstatus_q.mpp':'priv_lvl_e','cs_registers_i.priv_mode_id_o':'priv_lvl_e'}
    if name.startswith('cp_priv_lvl_'): typed[name]='priv_lvl_e'
    if name.startswith('cp_req_type_'): typed[name]='pmp_req_e'
    if name in typed:
        return sorted(set(v for _,v in TYPES[typed[name]]))
    if name=='cp_dummy_instr_mask': return list(range(8))
    if name=='cp_dummy_instr_type': return list(range(4))
    if name=='cp_napot_addr_modes': return list(range(32))
    # Every remaining explicit point or raw cross operand is a one-bit logic expression.
    # This whitelist prevents silently assigning a guessed width to future additions.
    boolean={'cp_wb_reg_no_load_hz','cp_mem_raw_hz','cp_mprv','cp_ls_error_exception',
        'cp_ls_pmp_exception','cp_branch_taken','cp_branch_not_taken','cp_data_ind_timing',
        'cp_dummy_instr_en','cp_dummy_instr_if_stage','cp_dummy_instr_id_stage',
        'cp_dummy_instr_wb_stage','cp_irq_pending','cp_debug_req','cp_debug_mode',
        'cp_nmi_taken','cp_misaligned_first_data_bus_err','cp_misaligned_second_data_bus_err',
        'cp_imem_response_latency','cp_dmem_response_latency','cp_warl_check_pmpcfg',
        'cp_rlb','cp_mmwp','cp_mml','cp_wdata_rlb','cp_wdata_mmwp','cp_wdata_mml',
        'cp_pmp_iside_region_override','cp_pmp_iside2_region_override','cp_pmp_dside_region_override',
        'dm_fetch_iside_debug_mode_cp','dm_fetch_iside2_debug_mode_cp','dm_load_store_debug_mode_cp',
        'id_stage_i.instr_fetch_err_i','id_stage_i.instr_fetch_err_plus2_i',
        'cs_registers_i.mstatus_q.mie','instr_unstalled_last','instr_unstalled',
        'fcov_rf_ecc_err_a_id','fcov_rf_ecc_err_b_id','pmp_iside_req_err','pmp_iside2_req_err',
        'pmp_dside_req_err','csr_pmp_mseccfg.rlb','pmp_current_priv_req_err',
        'if_stage_i.instr_is_compressed_out','misaligned_pmp_err_last',
        'load_store_unit_i.fcov_ls_mis_pmp_err_2','pmp_iside_access_fault_check',
        'pmp_iside2_access_fault_check','pmp_dside_access_fault_check'}
    if name not in boolean: raise ValueError('Unreviewed domain: '+group+'/'+name)
    return [0,1]

def header_body(sv):
    par=0
    for i,c in enumerate(sv):
        if c=='(': par+=1
        elif c==')': par-=1
        elif c=='{' and not par: return sv[:i].strip(),sv[i+1:-1]
    return sv.rstrip(';').strip(),''

def split_gate(expr):
    m=re.search(r'\biff\s*\(',expr)
    if not m: return expr.strip(),None
    p=expr.index('(',m.start()); e=balanced(expr,p)
    return expr[:m.start()].strip(),expr[p+1:e-1].strip()

def bin_clauses(body):
    out=[]
    for m in re.finditer(r'\b(?:(wildcard)\s+)?(illegal_bins|ignore_bins|bins)\s+(\w+)(\[\])?\s*=\s*(.*?);',body,re.S):
        expr,gate=split_gate(m[5])
        out.append({'wildcard':bool(m[1]),'type':m[2],'name':m[3],'array':bool(m[4]),'expr':expr,'gate':gate})
    return out

BINOPS={ast.BitAnd:operator.and_,ast.BitOr:operator.or_,ast.RShift:operator.rshift,ast.LShift:operator.lshift,
        ast.Add:operator.add,ast.Sub:operator.sub}
CMPOPS={ast.Eq:operator.eq,ast.NotEq:operator.ne,ast.Lt:operator.lt,ast.Gt:operator.gt,
        ast.LtE:operator.le,ast.GtE:operator.ge}

def selection(expression):
    """Compile the subset of cross-bin select expressions used by these files."""
    s=expression
    s=re.sub(r'(!?)\s*binsof\(([^)]+)\)\s*intersect\s*\{([^}]+)\}',
             lambda m: ('not ' if m[1] else '')+'S('+repr(m[2].strip())+','+repr(expand_set(m[3]))+')',s)
    s=re.sub(r'binsof\([^)]+\)','True',s)
    s=re.sub(r"\d+'[bBoOdDhH][0-9a-fA-F_]+",lambda m:str(number(m[0])),s)
    s=s.replace('&&',' and ').replace('||',' or ')
    s=re.sub(r'\bwith\b',' and ',s)
    s=re.sub(r'(?<![\w)])\|\s*\(', '(',s) # scalar reduction OR in one PMP filter
    s=re.sub(r'!(?!=)',' not ',s).strip()
    # Only identifiers outside strings may be rewritten.
    tree=ast.parse(' '.join(s.split()),mode='eval').body
    def run(node,values,domains):
        if isinstance(node,ast.Constant): return node.value
        if isinstance(node,ast.Str): return node.s
        if isinstance(node,ast.Num): return node.n
        if isinstance(node,ast.NameConstant): return node.value
        if isinstance(node,ast.List): return [run(x,values,domains) for x in node.elts]
        if isinstance(node,ast.Name):
            if node.id in CONSTANTS: return CONSTANTS[node.id]
            return values[node.id]
        if isinstance(node,ast.Attribute):
            def name(n): return n.id if isinstance(n,ast.Name) else name(n.value)+'.'+n.attr
            return values[name(node)]
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.Not): return not run(node.operand,values,domains)
        if isinstance(node,ast.BoolOp):
            return (all if isinstance(node.op,ast.And) else any)(run(x,values,domains) for x in node.values)
        if isinstance(node,ast.BinOp) and type(node.op) in BINOPS: return BINOPS[type(node.op)](run(node.left,values,domains),run(node.right,values,domains))
        if isinstance(node,ast.Compare):
            a=run(node.left,values,domains)
            for op,bn in zip(node.ops,node.comparators):
                b=run(bn,values,domains)
                if not CMPOPS[type(op)](a,b): return False
                a=b
            return True
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='S':
            key=run(node.args[0],values,domains); wanted=set(run(node.args[1],values,domains))
            return bool(set(domains[key]) & wanted)
        raise ValueError('Unsupported expression node: '+ast.dump(node))
    return lambda values,domains:bool(run(tree,values,domains))

def cp_bins(record):
    if record['kind']=='expression': return [{'label':'seen','values':[1]}]
    header,body=header_body(record['sv']); clauses=bin_clauses(body)
    positive=[x for x in clauses if x['type']=='bins' and x['expr']!='default']
    if positive:
        out=[]
        for clause in positive:
            expr=clause['expr']
            if '=>' in expr:
                a,b=expr.strip('() ').split('=>'); out.append({'label':clause['name'],'transition':[a.strip(),b.strip()]})
            else:
                vals=expand_set(expr,clause['wildcard'])
                if clause['array']: out.extend({'label':clause['name']+'['+str(v)+']','values':[v]} for v in vals)
                else: out.append({'label':clause['name'],'values':vals})
        return out
    domain=scalar_domain(record['group'],record['name'])
    removed=set()
    for c in clauses:
        if c['type']!='bins' and c['expr'] not in ('default','default sequence'): removed.update(expand_set(c['expr'],c['wildcard']))
    return [{'label':str(v),'values':[v]} for v in domain if v not in removed]

def elaborate(records=None):
    records=records or load_records(); defs={}; output=[]
    for r in records:
        r=dict(r)
        if r['kind']=='expression': r['gate']=None
        else:
            header,body=header_body(r['sv']); _,r['gate']=split_gate(header)
        if r['kind']!='cross':
            r['bins']=cp_bins(r); defs[r['id']]=r
            for b in r['bins']: output.append({'id':r['id']+'/'+b['label'],'declaration':r['id'],'bin':b,'group':r['group'],'kind':r['kind'],'line':r['line'],'file':r['file']})
    for r0 in records:
        if r0['kind']!='cross': continue
        r=dict(r0); header,body=header_body(r['sv']); head,r['gate']=split_gate(header)
        dims=split_top(re.split(r'\bcross\b',head,1)[1]); r['dimensions']=dims
        domains=[]
        for dim in dims:
            cp=defs.get(r['group']+'/'+dim)
            domains.append(cp['bins'] if cp else [{'label':str(v),'values':[v]} for v in scalar_domain(r['group'],dim)])
        clauses=bin_clauses(body); selectors=[(c,selection(c['expr'])) for c in clauses]
        bins=[]; merged=collections.defaultdict(list)
        for combination in itertools.product(*domains):
            values={k:b.get('values',[0])[0] for k,b in zip(dims,combination)}
            domain={k:b.get('values',[0]) for k,b in zip(dims,combination)}
            matching=[c for c,pred in selectors if pred(values,domain)]
            if any(c['type'] in ('illegal_bins','ignore_bins') for c in matching): continue
            label='|'.join(k+'='+b['label'] for k,b in zip(dims,combination))
            named=[c for c in matching if c['type']=='bins']
            if named:
                for c in named: merged[c['name']].append({'label':label,'dimensions':dict(zip(dims,combination)),'gate':c['gate']})
            else: bins.append({'label':label,'dimensions':dict(zip(dims,combination))})
        bins.extend({'label':k,'alternatives':v,'gate':v[0]['gate']} for k,v in merged.items())
        r['bins']=bins; defs[r['id']]=r
        for b in bins: output.append({'id':r['id']+'/'+b['label'],'declaration':r['id'],'bin':b,'group':r['group'],'kind':'cross','line':r['line'],'file':r['file']})
    return defs,output

class CoverageModel:
    """Sample one already-clocked observer transaction for a selected covergroup.

    values contains point names/raw operand names; enabled contains gate answers
    keyed by declaration ID. For transitions pass current enum SYMBOL (not number).
    The adapter owns reset and helpers from SV always blocks. reset() clears only
    sampling history; it never clears the cumulative covered set.
    """
    def __init__(self):
        self.defs,self.targets=elaborate(); self.hits=collections.Counter(); self.previous={}
        self.observed=set(); self.missing_inputs=collections.Counter()
    def reset(self): self.previous.clear()
    def sample(self,group,values,enabled=None,instance=0):
        enabled=enabled or {}; active={}; suffix=f'@{instance}' if group=='pmp_region_cg' else ''
        def allowed(r):
            if not r['gate']: return True
            if r['id'] not in enabled:
                self.missing_inputs['gate:'+r['id']]+=1; return None
            return bool(enabled[r['id']])
        def match(b,v,prev=None):
            return ([prev,v]==b['transition']) if 'transition' in b else v in b['values']
        for key,r in self.defs.items():
            if r['group']!=group or r['kind']=='cross': continue
            gate=allowed(r)
            if gate is False: active[r['name']]=[]; self.observed.add(key+suffix); continue
            if gate is None: continue
            if r['name'] not in values: self.missing_inputs['value:'+key]+=1; continue
            v=values[r['name']]; prev=self.previous.get(key+suffix)
            active[r['name']]=[b for b in r['bins'] if match(b,v,prev)]
            self.observed.add(key+suffix); self.previous[key+suffix]=v
            for b in active[r['name']]: self.hits[key+'/'+b['label']+suffix]+=1
        for key,r in self.defs.items():
            if r['group']!=group or r['kind']!='cross': continue
            gate=allowed(r)
            if gate is False: self.observed.add(key+suffix); continue
            if gate is None: continue
            choices={}; unknown=False
            for d in r['dimensions']:
                if group+'/'+d in self.defs:
                    if d not in active: unknown=True; break
                    choices[d]={b['label'] for b in active[d]}
                elif d not in values: unknown=True; break
                else: choices[d]={str(values[d])}
            if unknown: self.missing_inputs['cross:'+key]+=1; continue
            self.observed.add(key+suffix)
            for b in r['bins']:
                alternatives=b.get('alternatives',[b])
                if b.get('gate') and not enabled.get(key+'/'+b['label'],False): continue
                if any(all(spec['label'] in choices[d] for d,spec in alt['dimensions'].items()) for alt in alternatives): self.hits[key+'/'+b['label']+suffix]+=1

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--output', type=pathlib.Path, required=True)
    output=parser.parse_args().output
    output.mkdir(parents=True, exist_ok=False)
    defs,targets=elaborate()
    (output/'ibex_bins.json').write_text(json.dumps(targets,indent=2),encoding='utf-8')
    rows=[{k:r[k] for k in ['id','declaration','group','kind','file','line']} for r in targets]
    with (output/'ibex_bins.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary={g:sum(r['group']==g for r in targets) for g in sorted({r['group'] for r in targets})}
    summary['total_type_bins']=len(targets)
    (output/'ibex_bin_counts.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
