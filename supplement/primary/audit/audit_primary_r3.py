from __future__ import annotations
from pathlib import Path
from bs4 import BeautifulSoup
import csv, hashlib, json, re, sys, html
METHOD=Path(__file__).resolve().parents[2]/'method'
sys.path.insert(0,str(METHOD))
from audit_rules import authority_consistency_check, conflict_routing_check, guard_semantics_check

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'artifact_28/dossiers'
GENLOG=ROOT/'artifact_28/generation.log'
OUT=Path(__file__).resolve().parent
NON={'genindex.html','search.html','raci_directory.html','discovery_report.html','index.html','extraction_review.html'}
CERT=['Certified metric dossier','certified formula','certifies the KPI definition','certified calculation expression','Print Certified Dossier','certified implementation path']
ROLE_PREFIX=('Source context:','KPI marker:','Calculation expression:','Calculation hint:','Scope boundary:','Query entry point:','Package boundary:','KPI function:','Output alias:','Source relation:','Execution delimiter:','Return contract:')
EXEC_ROLE=('Output alias:','Calculation expression:','Scope boundary:','Query entry point:','Package boundary:','KPI function:','Source relation:','Execution delimiter:','Return contract:')
CONFLICT_RE=re.compile(r'\bconflict\b|\bmismatch\b|\binverted\b',re.I)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(s):
    s=re.sub(r'([a-z0-9])([A-Z])',r'\1 \2',s)
    s=s.replace('_',' ')
    return ''.join(re.findall(r'[a-z0-9]+',s.lower()))
def soup_text(p):
    soup=BeautifulSoup(p.read_text(errors='ignore'),'html.parser')
    return soup,[x.strip() for x in soup.stripped_strings]
def next_after(xs,label):
    for i,x in enumerate(xs[:-1]):
        if x==label:return xs[i+1]
    return ''
def lineage_pairs(xs):
    out=[];seen=set()
    for i,x in enumerate(xs[:-1]):
        if re.match(r'^\d+\s*\|',x) and xs[i+1].startswith(ROLE_PREFIX):
            pair=(x,xs[i+1])
            if pair not in seen:out.append(pair);seen.add(pair)
    return out
def lineage_errors(pairs):
    out=[]
    for code,desc in pairs:
        raw=re.sub(r'^\d+\s*\|\s*','',code).strip()
        is_comment=raw.startswith(('#','//','--','*',"'",'"""',"'''"))
        if is_comment and desc.startswith(EXEC_ROLE):
            out.append({'code':raw,'description':desc,'reason':'comment_or_docstring_assigned_executable_role'})
            continue
        if desc.startswith('Output alias:'):
            m=re.search(r'CAST\(.*?\s+AS\s+([A-Za-z0-9_(),]+)\)\s+AS\s+([A-Za-z_][A-Za-z0-9_]*)',raw,re.I)
            d=re.search(r'maps this expression to\s+([^\s]+)',desc,re.I)
            if m and d:
                typ=re.sub(r'\(.*','',m.group(1)).upper(); alias=m.group(2).upper(); described=d.group(1).strip('.,').upper()
                if described==typ and described!=alias:
                    out.append({'code':raw,'description':desc,'reason':'cast_type_labeled_as_output_alias','actual_alias':m.group(2)})
    return out

def source_code(soup):
    pres=soup.find_all('pre')
    if not pres:return ''
    # Longest raw source panel; numbered inline snippets are shorter.
    return html.unescape(html.unescape(max((p.get_text('\n') for p in pres), key=len)))

def zero_guard_candidates(code):
    found=[]
    # SQL NULLIF denominator guards.
    for m in re.finditer(r'NULLIF\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*0(?:\.0+)?\s*\)',code,re.I):
        found.append({'text':m.group(0),'variable':m.group(1),'kind':'zero','construct':'NULLIF'})
    # IF-family comparisons with literal zero. Keep one item per exact conditional line.
    for line in code.splitlines():
        if not re.search(r'\bif\b',line,re.I):continue
        if re.search(r'\bNULLIF\b',line,re.I):continue
        m=re.search(r'([A-Za-z_][A-Za-z0-9_]*)\s*(<=|>=|==|=|<|>)\s*0(?:\.0+)?',line,re.I)
        if not m:continue
        op=m.group(2)
        kind='nonpositive' if op in {'<=','>'} else ('zero' if op in {'==','='} else 'other')
        found.append({'text':line.strip().rstrip(':'),'variable':m.group(1),'kind':kind,'operator':op,'construct':'IF'})
    # Deduplicate same semantic guard if repeated in source panels.
    out=[];seen=set()
    for x in found:
        key=(canon(x['variable']),x['kind'],x.get('operator',''),x['construct'])
        if key not in seen:out.append(x);seen.add(key)
    return out

def guard_verdict(xs,guard):
    denominator=next_after(xs,'Denominator:')
    safeguard=next_after(xs,'Zero-Division Guard:')
    ok,reason=guard_semantics_check(guard['variable'],guard['kind'],denominator,safeguard)
    return ok,denominator,reason

prepared=re.findall(r"Prepared dossier for '([^']+)'",GENLOG.read_text(errors='ignore'))
files=sorted(p for p in BUILD.glob('*.html') if p.name not in NON)
assert len(prepared)==28 and len(files)==28
rows=[];role_detail=[];guard_detail=[]
for p in files:
    soup,xs=soup_text(p); full='\n'.join(xs); pairs=lineage_pairs(xs); errs=lineage_errors(pairs)
    if errs:role_detail.append({'dossier':p.name,'errors':errs})
    code=source_code(soup)
    guards=zero_guard_candidates(code)
    gfail=0;gpres=0
    for g in guards:
        ok,den,reason=guard_verdict(xs,g)
        gpres+=int(ok);gfail+=int(not ok)
        guard_detail.append({'dossier':p.name,'source_condition':g['text'],'guarded_variable':g['variable'],'guard_kind':g['kind'],'displayed_denominator':den,'verdict':'preserved' if ok else 'failure','reason':reason})
    status='Needs Review' if 'Needs Review' in xs else ('Validated' if 'Validated' in xs else 'Unknown')
    source='\n'.join(re.sub(r'^\d+\s*\|\s*','',a) for a,_ in pairs)
    explicit=bool(CONFLICT_RE.search(source))
    rq='Review Queue' in xs
    cert=[c for c in CERT if c.lower() in full.lower()]
    rows.append({'dossier':p.name,'sha256_html':sha(p),'status':status,'lineage_typing_defect':bool(errs),'lineage_error_instances':len(errs),'guard_instances':len(guards),'guard_preserved':gpres,'guard_failures':gfail,'guard_binding_defect':gfail>0,'explicit_conflict':explicit,'conflict_routing_ok':conflict_routing_check(explicit,status,rq)=='PASS','authority_applicable':status=='Needs Review','authority_language_defect':authority_consistency_check(status,cert)=='FAIL','certification_phrases':' | '.join(cert)})

# R3 primary invariants. The threshold branch from R2 is intentionally excluded from guard scope.
assert len(rows)==28
assert sum(r['status']=='Needs Review' for r in rows)==19
assert sum(r['status']=='Validated' for r in rows)==9
assert sum(r['lineage_typing_defect'] for r in rows)==4
assert sum(r['lineage_error_instances'] for r in rows)==12
assert sum(r['guard_instances'] for r in rows)==10
assert sum(r['guard_preserved'] for r in rows)==5
assert sum(r['guard_failures'] for r in rows)==5
assert sum(r['guard_binding_defect'] for r in rows)==5
assert sum(r['explicit_conflict'] for r in rows)==6
assert sum(r['conflict_routing_ok'] for r in rows)==6
assert sum(r['authority_language_defect'] for r in rows)==19

with (OUT/'dossier_audit_28_r3.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
with (OUT/'guard_audit_10_r3.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(guard_detail[0]));w.writeheader();w.writerows(guard_detail)
(OUT/'lineage_defect_details_r3.json').write_text(json.dumps(role_detail,indent=2)+'\n')
summary={
 'corpus':{'dossiers':28,'needs_review':19,'validated':9,'generation_log_sha256':sha(GENLOG)},
 'defect_classes':{
   'lineage_typing':{'class_count':1,'affected_dossiers':sum(r['lineage_typing_defect'] for r in rows),'visible_instances':sum(r['lineage_error_instances'] for r in rows),'dossiers':[r['dossier'] for r in rows if r['lineage_typing_defect']]},
   'guard_to_safeguard_binding':{'class_count':1,'guard_instances':sum(r['guard_instances'] for r in rows),'affected_dossiers':sum(r['guard_binding_defect'] for r in rows),'failure_instances':sum(r['guard_failures'] for r in rows),'preserved_instances':sum(r['guard_preserved'] for r in rows)},
   'authority_language_template':{'class_count':1,'eligible_unresolved_dossiers':19,'affected_dossiers':19}
 },
 'working_mechanism':{'conflict_routing':{'class_count':1,'eligible_explicit_conflict_dossiers':6,'preserved_dossiers':6}},
 'interpretation':'Three systematic generator/template defect classes plus one correctly operating conflict-routing mechanism; dossier/guard counts are repeated manifestations, not independent prevalence estimates.'
}
(OUT/'audit_summary_r3.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
