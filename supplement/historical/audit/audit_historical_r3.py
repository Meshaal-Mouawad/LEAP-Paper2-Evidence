from pathlib import Path
from bs4 import BeautifulSoup
import csv, hashlib, html, json, re, sys
METHOD=Path(__file__).resolve().parents[2]/'method'
sys.path.insert(0,str(METHOD))
from audit_rules import authority_consistency_check, conflict_routing_check, guard_semantics_check
CERT=['Certified metric dossier','certified formula','certifies the KPI definition','certified calculation expression','Print Certified Dossier','certified implementation path']
ROLE_PREFIX=('Source context:','KPI marker:','Calculation expression:','Calculation hint:','Scope boundary:','Query entry point:','Package boundary:','KPI function:','Output alias:','Source relation:','Execution delimiter:','Return contract:')
EXEC_ROLE=('Output alias:','Calculation expression:','Scope boundary:','Query entry point:','Package boundary:','KPI function:','Source relation:','Execution delimiter:','Return contract:')
NON={'genindex.html','search.html','raci_directory.html','discovery_report.html','index.html','extraction_review.html','kpi.html'}
CONFLICT_RE=re.compile(r'\bconflict\b|\bmismatch\b|\binverted\b',re.I)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(s):
 s=re.sub(r'([a-z0-9])([A-Z])',r'\1 \2',s).replace('_',' '); return ''.join(re.findall(r'[a-z0-9]+',s.lower()))
def next_after(xs,label):
 for i,x in enumerate(xs[:-1]):
  if x==label:return xs[i+1]
 return ''
def pairs(xs):
 o=[];seen=set()
 for i,x in enumerate(xs[:-1]):
  if re.match(r'^\d+\s*\|',x) and xs[i+1].startswith(ROLE_PREFIX):
   k=(x,xs[i+1])
   if k not in seen:o.append(k);seen.add(k)
 return o
def role_errors(ps):
 o=[]
 for code,desc in ps:
  raw=re.sub(r'^\d+\s*\|\s*','',code).strip(); com=raw.startswith(('#','//','--','*',"'",'"""',"'''"))
  if com and desc.startswith(EXEC_ROLE):o.append({'code':raw,'description':desc,'reason':'comment_or_docstring_assigned_executable_role'});continue
  if desc.startswith('Output alias:'):
   m=re.search(r'CAST\(.*?\s+AS\s+([A-Za-z0-9_(),]+)\)\s+AS\s+([A-Za-z_][A-Za-z0-9_]*)',raw,re.I);d=re.search(r'maps this expression to\s+([^\s]+)',desc,re.I)
   if m and d:
    typ=re.sub(r'\(.*','',m.group(1)).upper();alias=m.group(2).upper();des=d.group(1).strip('.,').upper()
    if des==typ and des!=alias:o.append({'code':raw,'description':desc,'reason':'cast_type_labeled_as_output_alias','actual_alias':m.group(2)})
 return o
def guards(soup):
 pres=soup.find_all('pre'); code=html.unescape(html.unescape(max((p.get_text('\n') for p in pres),key=len,default='')));out=[]
 for m in re.finditer(r'NULLIF\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*0(?:\.0+)?\s*\)',code,re.I):out.append({'text':m.group(0),'variable':m.group(1),'kind':'zero'})
 for line in code.splitlines():
  if not re.search(r'\bif\b',line,re.I) or re.search(r'\bNULLIF\b',line,re.I):continue
  m=re.search(r'([A-Za-z_][A-Za-z0-9_]*)\s*(<=|==|=)\s*0(?:\.0+)?',line,re.I)
  if m:out.append({'text':line.strip(),'variable':m.group(1),'kind':'nonpositive' if m.group(2)=='<=' else 'zero'})
 z=[];seen=set()
 for g in out:
  k=(canon(g['variable']),g['kind'])
  if k not in seen:z.append(g);seen.add(k)
 return z
def main(build,out):
 build=Path(build);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 files=[p for p in sorted(build.glob('*.html')) if p.name not in NON]
 rows=[];gdetails=[];rdetails=[]
 for p in files:
  soup=BeautifulSoup(p.read_text(errors='ignore'),'html.parser');xs=[x.strip() for x in soup.stripped_strings];full='\n'.join(xs);ps=pairs(xs);es=role_errors(ps)
  if es: rdetails.append({'dossier':p.name,'errors':es})
  gs=guards(soup); den=next_after(xs,'Denominator:'); safeguard=next_after(xs,'Zero-Division Guard:')
  gf=gp=0
  for g in gs:
   ok,reason=guard_semantics_check(g['variable'],g['kind'],den,safeguard)
   gf+=int(not ok);gp+=int(ok);gdetails.append({'dossier':p.name,**g,'displayed_denominator':den,'verdict':'preserved' if ok else 'failure','reason':reason})
  st='Needs Review' if 'Needs Review' in xs else ('Validated' if 'Validated' in xs else 'Unknown'); source='\n'.join(re.sub(r'^\d+\s*\|\s*','',a) for a,_ in ps);explicit=bool(CONFLICT_RE.search(source));rq='Review Queue' in xs;cert=[c for c in CERT if c.lower() in full.lower()]
  rows.append({'dossier':p.name,'sha256':sha(p),'status':st,'lineage_defect':bool(es),'lineage_instances':len(es),'guard_instances':len(gs),'guard_failures':gf,'guard_preserved':gp,'explicit_conflict':explicit,'conflict_routing_ok':conflict_routing_check(explicit,st,rq)=='PASS','authority_defect':authority_consistency_check(st,cert)=='FAIL'})
 summary={'dossiers':len(rows),'needs_review':sum(r['status']=='Needs Review' for r in rows),'validated':sum(r['status']=='Validated' for r in rows),'lineage':{'affected_dossiers':sum(r['lineage_defect'] for r in rows),'instances':sum(r['lineage_instances'] for r in rows)},'guards':{'instances':sum(r['guard_instances'] for r in rows),'failures':sum(r['guard_failures'] for r in rows),'preserved':sum(r['guard_preserved'] for r in rows)},'authority':{'eligible':sum(r['status']=='Needs Review' for r in rows),'affected':sum(r['authority_defect'] for r in rows)},'conflict_routing':{'eligible':sum(r['explicit_conflict'] for r in rows),'preserved':sum(r['conflict_routing_ok'] for r in rows)}}
 with (out/'historical_dossiers.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 with (out/'historical_guards.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(gdetails[0]));w.writeheader();w.writerows(gdetails)
 (out/'historical_lineage.json').write_text(json.dumps(rdetails,indent=2)+'\n');(out/'historical_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
