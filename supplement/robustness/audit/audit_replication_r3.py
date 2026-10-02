from pathlib import Path
from bs4 import BeautifulSoup
import csv,json,re,html,hashlib,sys
METHOD=Path(__file__).resolve().parents[2]/'method'
sys.path.insert(0,str(METHOD))
from audit_rules import authority_consistency_check, conflict_routing_check, guard_semantics_check

CERT=['Certified metric dossier','certified formula','certifies the KPI definition','certified calculation expression','Print Certified Dossier','certified implementation path']
EXEC_PREFIX=('Output alias:','Calculation expression:','Scope boundary:','Query entry point:','Package boundary:','KPI function:','Source relation:','Execution delimiter:','Return contract:')
EXCLUDE={'index.rst','discovery_report.rst','extraction_review.rst','raci_directory.rst'}

def canon(s):
    s=re.sub(r'([a-z0-9])([A-Z])',r'\1 \2',s).replace('_',' ')
    return ''.join(re.findall(r'[a-z0-9]+',s.lower()))

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def parse_page(p):
    raw=p.read_text(errors='ignore')
    soup=BeautifulSoup(raw,'html.parser')
    text='\n'.join(soup.stripped_strings)
    # source file
    sf=''
    lab=soup.find(string=lambda x:isinstance(x,str) and x.strip()=='Source File')
    if lab:
        par=lab.parent.parent if lab.parent else None
        if par:
            st=par.find('strong'); sf=st.get_text(' ',strip=True) if st else ''
    # status
    header=soup.find(attrs={'data-governance-status':True})
    status=header.get('data-governance-status') if header else ('Needs Review' if 'Needs Review' in text else ('Validated' if 'Validated' in text else 'Unknown'))
    # lineage
    errors=[]
    for row in soup.select('.leap-code-lineage-row'):
        c=row.select_one('.leap-code-lineage-code'); d=row.select_one('.leap-code-lineage-role')
        if not c or not d: continue
        code=html.unescape(c.get_text(' ',strip=True)); desc=d.get_text(' ',strip=True)
        code=re.sub(r'^\d+\s*\|\s*','',code).strip()
        is_comment=code.startswith(('#','//','--','*',"'",'"""',"'''"))
        if is_comment and desc.startswith(EXEC_PREFIX):
            errors.append({'code':code,'description':desc,'reason':'comment_or_docstring_assigned_executable_role'})
            continue
        if desc.startswith('Output alias:'):
            m=re.search(r'CAST\(.*?\s+AS\s+([A-Za-z0-9_(),]+)\)\s+AS\s+([A-Za-z_][A-Za-z0-9_]*)',code,re.I)
            dm=re.search(r'maps this expression to\s+([^\s]+)',desc,re.I)
            if m and dm:
                typ=re.sub(r'\(.*','',m.group(1)).upper(); alias=m.group(2).upper(); described=dm.group(1).strip('.,').upper()
                if described==typ and described!=alias:
                    errors.append({'code':code,'description':desc,'reason':'cast_type_labeled_as_output_alias','actual_alias':m.group(2)})
    # Same lineage block is rendered twice in the dossier source; count each visible code/role pair once.
    dedup=[]; seen_err=set()
    for e in errors:
        k=(e.get('code',''),e.get('description',''),e.get('reason',''),e.get('actual_alias',''))
        if k not in seen_err:
            dedup.append(e); seen_err.add(k)
    errors=dedup
    # source code longest font mono pre
    pres=soup.select('pre.font-mono') or soup.find_all('pre')
    code=max((html.unescape(html.unescape(x.get_text('\n'))) for x in pres),key=len,default='')
    guards=[]
    for m in re.finditer(r'NULLIF\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*0(?:\.0+)?\s*\)',code,re.I):
        guards.append({'text':m.group(0),'variable':m.group(1),'kind':'zero'})
    for line in code.splitlines():
        if not re.search(r'\bif\b',line,re.I) or re.search(r'\bNULLIF\b',line,re.I): continue
        m=re.search(r'([A-Za-z_][A-Za-z0-9_]*)\s*(<=|==|=)\s*0(?:\.0+)?',line,re.I)
        if m: guards.append({'text':line.strip(),'variable':m.group(1),'kind':'nonpositive' if m.group(2)=='<=' else 'zero'})
    # semantic dedupe
    dg=[]; seen=set()
    for g in guards:
        k=(canon(g['variable']),g['kind'])
        if k not in seen: dg.append(g); seen.add(k)
    guards=dg
    # denominator
    den=''
    den_node=soup.find(['i','b'],string=lambda x:isinstance(x,str) and x.strip()=='Denominator:')
    if den_node:
        sib=den_node.next_sibling
        if sib is not None: den=str(sib).strip()
    if not den:
        denstr=soup.find(string=lambda x:isinstance(x,str) and x.strip().startswith('Denominator:'))
        if denstr: den=denstr.strip().split(':',1)[1].strip()
    # logic safeguard text and direct safeguard sentence
    logic=''
    lab=soup.find(string=lambda x:isinstance(x,str) and x.strip()=='Logic Safeguards')
    if lab:
        anc=lab.parent
        for _ in range(4):
            if anc and anc.parent: anc=anc.parent
        if anc: logic=anc.get_text(' ',strip=True)
    safeguard=''
    zlab=soup.find(string=lambda x:isinstance(x,str) and x.strip()=='Zero-Division Guard:')
    if zlab:
        parent=zlab.parent
        container=parent.parent if parent and parent.parent else parent
        if container:
            parts=[x.strip() for x in container.stripped_strings]
            try:
                j=parts.index('Zero-Division Guard:'); safeguard=parts[j+1] if j+1<len(parts) else ''
            except ValueError: pass
    gdetail=[]
    for g in guards:
        ok,reason=guard_semantics_check(g['variable'],g['kind'],den,safeguard)
        gdetail.append({**g,'displayed_denominator':den,'verdict':'preserved' if ok else 'failure','reason':reason})
    conflict_signal='Governance Conflict Flag:' in logic or 'Conflict detected. See Review Queue' in text
    review_queue='Review Queue' in text
    cert=[c for c in CERT if c.lower() in text.lower()]
    return {'page':p.name,'source_file':sf,'sha256':sha(p),'status':status,'role_defect':bool(errors),'role_instances':len(errors),'role_errors':errors,'guards':gdetail,'guard_instances':len(gdetail),'guard_failures':sum(g['verdict']=='failure' for g in gdetail),'conflict_signal':conflict_signal,'conflict_routing_ok':conflict_routing_check(conflict_signal,status,review_queue)=='PASS','authority_defect':authority_consistency_check(status,cert)=='FAIL','certification_phrases':cert}

def main(root,out,label):
    root=Path(root); out=Path(out); out.mkdir(parents=True,exist_ok=True)
    pages=sorted(p for p in (root/'docs').glob('*.rst') if p.name not in EXCLUDE and p.name not in {'conf.py'})
    rows=[parse_page(p) for p in pages]
    # filter only actual dossier page sources: generated dossiers have Source File field
    rows=[r for r in rows if r['source_file']]
    detail=[]
    for r in rows:
        for g in r['guards']: detail.append({'page':r['page'],'source_file':r['source_file'],**g})
    csvrows=[{k:v for k,v in r.items() if k not in {'role_errors','guards','certification_phrases'}} for r in rows]
    with (out/f'{label}_dossiers.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(csvrows[0]));w.writeheader();w.writerows(csvrows)
    if detail:
        with (out/f'{label}_guards.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(detail[0]));w.writeheader();w.writerows(detail)
    summary={
      'label':label,'dossiers':len(rows),
      'status':{'needs_review':sum(r['status']=='Needs Review' for r in rows),'validated':sum(r['status']=='Validated' for r in rows)},
      'lineage_typing':{'affected_dossiers':sum(r['role_defect'] for r in rows),'visible_instances':sum(r['role_instances'] for r in rows)},
      'guard_binding':{'guard_instances':sum(r['guard_instances'] for r in rows),'affected_dossiers':sum(r['guard_failures']>0 for r in rows),'failure_instances':sum(r['guard_failures'] for r in rows),'preserved_instances':sum(r['guard_instances']-r['guard_failures'] for r in rows)},
      'authority_language':{'eligible_needs_review':sum(r['status']=='Needs Review' for r in rows),'affected_dossiers':sum(r['authority_defect'] for r in rows)},
      'conflict_routing':{'eligible_conflict_signal':sum(r['conflict_signal'] for r in rows),'preserved':sum(r['conflict_routing_ok'] for r in rows)},
      'role_detail':[{'page':r['page'],'source_file':r['source_file'],'errors':r['role_errors']} for r in rows if r['role_errors']]
    }
    (out/f'{label}_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    if len(sys.argv)!=4: raise SystemExit('usage: audit_replication_r3.py BUILD_ROOT OUT_DIR LABEL')
    main(*sys.argv[1:])
