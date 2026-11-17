"""Executable, source-traceable Python representation of the Ibex fcov plan.

This parses the official coverage declarations, NOT prose bullets as bins.
Sources are pinned in targets/ibex/coverage/reference. The evaluator is in
lumen.coverage.definitions; this exporter never executes untrusted source text.
"""
from __future__ import annotations
import argparse, collections, csv, hashlib, json, pathlib, re

from lumen.paths import FCOV

def decomment(text):
    def blank(m): return ''.join('\n' if c == '\n' else ' ' for c in m[0])
    return re.sub(r'/\*.*?\*/|//[^\n]*', blank, text, flags=re.S)

def balanced(text, start, left='(', right=')'):
    assert text[start] == left
    depth=0
    for i in range(start,len(text)):
        if text[i]==left: depth+=1
        elif text[i]==right:
            depth-=1
            if not depth: return i+1
    raise ValueError('Unbalanced source')

def split_top(text, sep=','):
    result=[]; start=0; depth=0
    for i,c in enumerate(text):
        if c in '([{': depth+=1
        elif c in ')]}': depth-=1
        elif c==sep and depth==0: result.append(text[start:i].strip()); start=i+1
    result.append(text[start:].strip())
    return result

def declarations(path):
    original=path.read_text(encoding='utf-8'); src=decomment(original)
    records=[]
    for gm in re.finditer(r'\bcovergroup\s+(\w+).*?;',src,flags=re.S):
        group=gm[1]; end=src.index('endgroup',gm.end()); chunk=src[gm.end():end]
        pattern=r'(?P<label>\b\w+)\s*:\s*(?P<kind>coverpoint|cross)\b|`DV_FCOV_EXPR_SEEN\s*\('
        for m in re.finditer(pattern,chunk):
            pos=gm.end()+m.start()
            if not m['label']:
                start=src.index('(',pos); stop=balanced(src,start)
                args=split_top(src[start+1:stop-1]); name='cp_'+args[0]; kind='expression'
                declaration=src[pos:stop]
            else:
                name=m['label']; kind=m['kind']; i=gm.end()+m.end(); par=0
                while i<end:
                    c=src[i]
                    if c=='(': par+=1
                    elif c==')': par-=1
                    elif c=='{' and par==0:
                        i=balanced(src,i,'{','}'); break
                    elif c==';' and par==0: i+=1; break
                    i+=1
                stop=i; declaration=src[pos:stop]
            line=src.count('\n',0,pos)+1
            records.append({'id':group+'/'+name,'group':group,'name':name,'kind':kind,
                            'file':path.name,'line':line,'end_line':src.count('\n',0,stop)+1,
                            'sv':declaration.strip(),'source_sha256':hashlib.sha256(original.encode()).hexdigest()})
    return records

def load_records():
    base=FCOV
    return [r for p in sorted(base.glob('*_if.sv')) for r in declarations(p)]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output', type=pathlib.Path, required=True)
    output=parser.parse_args().output
    output.mkdir(parents=True, exist_ok=False)
    rows=load_records()
    (output/'ibex_declarations.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    with (output/'ibex_declarations.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=['id','kind','file','line','end_line','sv','source_sha256','group','name']); writer.writeheader(); writer.writerows(rows)
    counts={g:dict(collections.Counter(r['kind'] for r in rows if r['group']==g)) for g in sorted(set(r['group'] for r in rows))}
    print(json.dumps({'declaration_count':len(rows),'groups':counts},indent=2))

if __name__=='__main__': main()
