from __future__ import annotations
import copy, csv, hashlib, importlib.util, json, re, sys
from pathlib import Path
from fastapi.testclient import TestClient
import fastapi, pydantic

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'source'; GEN=ROOT/'generated'; AUD=ROOT/'audit'
METHOD=ROOT.parent/'method'
sys.path.insert(0,str(METHOD))
from audit_rules import compare_published_role

GEN.mkdir(exist_ok=True); AUD.mkdir(exist_ok=True)
FILES=['query_param_constraints.py','path_numeric_constraints.py','body_field_constraints.py','deprecated_operation.py']
UPSTREAM_COMMIT='33d411dbc3236275dd64d200bfe18d5d60a49b2e'
BLOB_SHA1={
 'query_param_constraints.py':'775095bda86ae8d0296d961eadc1e164d7016756',
 'path_numeric_constraints.py':'426ec3776446bb49092be1e511833cd6162b017a',
 'body_field_constraints.py':'c9d99e1c2b373bbaec9089715814655d98cc9a97',
 'deprecated_operation.py':'7c1aa9b206054df7a543d3b0b74621120ec8e3e1',
}
UPSTREAM_PATH={
 'query_param_constraints.py':'docs_src/query_params_str_validations/tutorial010_an_py310.py',
 'path_numeric_constraints.py':'docs_src/path_params_numeric_validations/tutorial006_an_py310.py',
 'body_field_constraints.py':'docs_src/body_fields/tutorial001_an_py310.py',
 'deprecated_operation.py':'docs_src/path_operation_configuration/tutorial006_py310.py',
}

def sha256(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def git_blob_sha1(p:Path):
    b=p.read_bytes(); return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def load(path:Path):
    name='ext_'+path.stem
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod)
    return mod
def str_branch(schema): return next((x for x in schema.get('anyOf',[]) if x.get('type')=='string'),schema)
def src(fn): return (SRC/fn).read_text()
def need(pattern,text,label):
    m=re.search(pattern,text,re.S)
    if not m: raise SystemExit(f'source expectation not found: {label}')
    return m

def role_result(expected_location,expected_name,p):
    ok,reason=compare_published_role(expected_location,expected_name,p.get('in',''),p.get('name',''))
    return ok,reason

# Verify frozen external source identity before generation.
provenance={}
for fn in FILES:
    p=SRC/fn; got=git_blob_sha1(p); exp=BLOB_SHA1[fn]
    if got!=exp: raise SystemExit(f'Git blob mismatch: {fn}: {got} != {exp}')
    provenance[fn]={'upstream_path':UPSTREAM_PATH[fn],'git_blob_sha1':got,'sha256':sha256(p)}

schemas={}; runtime={}
for fn in FILES:
    p=SRC/fn; mod=load(p); schema=mod.app.openapi(); schemas[fn]=schema
    (GEN/(p.stem+'.openapi.json')).write_text(json.dumps(schema,indent=2,sort_keys=True)+'\n')
    client=TestClient(mod.app)
    if fn=='query_param_constraints.py':
        runtime[fn]={'valid':client.get('/items/',params={'item-query':'fixedquery'}).status_code,
                     'too_short':client.get('/items/',params={'item-query':'xx'}).status_code,
                     'pattern_fail':client.get('/items/',params={'item-query':'abc'}).status_code}
    elif fn=='path_numeric_constraints.py':
        runtime[fn]={'valid':client.get('/items/5',params={'q':'x','size':1.5}).status_code,
                     'path_low':client.get('/items/-1',params={'q':'x','size':1.5}).status_code,
                     'size_high':client.get('/items/5',params={'q':'x','size':11}).status_code}
    elif fn=='body_field_constraints.py':
        runtime[fn]={'valid':client.put('/items/1',json={'item':{'name':'x','description':'ok','price':1}}).status_code,
                     'price_fail':client.put('/items/1',json={'item':{'name':'x','price':0}}).status_code,
                     'description_fail':client.put('/items/1',json={'item':{'name':'x','description':'x'*301,'price':1}}).status_code}
    else:
        runtime[fn]={'elements':client.get('/elements/').status_code,'items':client.get('/items/').status_code}

rows=[]
def add(ex,obl,app,out,evidence,adapt='none'):
    rows.append({'example':ex,'obligation':obl,'applicable':str(app),'outcome':out,'evidence':evidence,'adaptation':adapt})

# Query parameter: read source expectation first, then compare generated role/name and constraints.
text=src('query_param_constraints.py')
alias=need(r'alias\s*=\s*[\"\']([^\"\']+)',text,'query alias').group(1)
minlen=int(need(r'min_length\s*=\s*(\d+)',text,'query min_length').group(1))
maxlen=int(need(r'max_length\s*=\s*(\d+)',text,'query max_length').group(1))
pattern=need(r'pattern\s*=\s*[\"\']([^\"\']+)',text,'query pattern').group(1)
s=schemas['query_param_constraints.py'];op=s['paths']['/items/']['get'];q=op['parameters'][0];qb=str_branch(q['schema'])
ok,reason=role_result('query',alias,q)
add('query_param_constraints','source-role accuracy',True,'PASS' if ok else 'FAIL',f"source expects query/{alias}; OpenAPI publishes {q.get('in')}/{q.get('name')}; {reason}")
ok=qb.get('minLength')==minlen and qb.get('maxLength')==maxlen and qb.get('pattern')==pattern and runtime['query_param_constraints.py']['too_short']==422 and runtime['query_param_constraints.py']['pattern_fail']==422
add('query_param_constraints','condition disclosure',True,'PASS' if ok else 'FAIL',f"source min/max/pattern={minlen}/{maxlen}/{pattern}; OpenAPI={qb.get('minLength')}/{qb.get('maxLength')}/{qb.get('pattern')}; invalid requests={runtime['query_param_constraints.py']['too_short']}/{runtime['query_param_constraints.py']['pattern_fail']}.",'Declarative validation constraints are used as the external condition representation.')
add('query_param_constraints','representation-disagreement preservation',False,'N/A','No unresolved explicit representation conflict exists in this official example.')
add('query_param_constraints','review-authority consistency',False,'N/A','No human review state exists in this official example.','No lifecycle-status substitution is counted as a direct pass.')

# Path/query roles and numeric constraints.
text=src('path_numeric_constraints.py')
need(r'@app\.get\([\"\']/items/\{item_id\}[\"\']\)',text,'path route')
need(r'item_id\s*:\s*Annotated\[int,\s*Path\(',text,'item_id Path role')
need(r'size\s*:\s*Annotated\[float,\s*Query\(',text,'size Query role')
path_min=float(need(r'Path\([^)]*?ge\s*=\s*([0-9.]+)',text,'path minimum').group(1))
path_max=float(need(r'Path\([^)]*?le\s*=\s*([0-9.]+)',text,'path maximum').group(1))
size_min=float(need(r'Query\([^)]*?gt\s*=\s*([0-9.]+)',text,'size minimum').group(1))
size_max=float(need(r'Query\([^)]*?lt\s*=\s*([0-9.]+)',text,'size maximum').group(1))
s=schemas['path_numeric_constraints.py'];op=s['paths']['/items/{item_id}']['get'];pars={p['name']:p for p in op['parameters']}
checks=[]
for name,loc in [('item_id','path'),('q','query'),('size','query')]:
    ok,reason=role_result(loc,name,pars[name]); checks.append((ok,reason))
ok=all(x[0] for x in checks)
add('path_numeric_constraints','source-role accuracy',True,'PASS' if ok else 'FAIL',f"source expects item_id/path, q/query, size/query; OpenAPI publishes item_id/{pars['item_id']['in']}, q/{pars['q']['in']}, size/{pars['size']['in']}.")
i=pars['item_id']['schema'];ss=pars['size']['schema'];ok=i.get('minimum')==path_min and i.get('maximum')==path_max and ss.get('exclusiveMinimum')==size_min and ss.get('exclusiveMaximum')==size_max and runtime['path_numeric_constraints.py']['path_low']==422 and runtime['path_numeric_constraints.py']['size_high']==422
add('path_numeric_constraints','condition disclosure',True,'PASS' if ok else 'FAIL',f"source item_id={path_min}..{path_max}, size>{size_min} and <{size_max}; OpenAPI item_id={i.get('minimum')}..{i.get('maximum')}, size={ss.get('exclusiveMinimum')}..{ss.get('exclusiveMaximum')}; invalid requests=422/422.",'Declarative validation constraints are used as the external condition representation.')
add('path_numeric_constraints','representation-disagreement preservation',False,'N/A','No unresolved explicit representation conflict exists in this official example.')
add('path_numeric_constraints','review-authority consistency',False,'N/A','No human review state exists in this official example.')

# Request body and field constraints.
text=src('body_field_constraints.py')
need(r'@app\.put\([\"\']/items/\{item_id\}[\"\']\)',text,'body route')
need(r'item\s*:\s*Annotated\[Item,\s*Body\(',text,'Item body role')
desc_max=int(need(r'description[^\n]*?max_length\s*=\s*(\d+)|description\s*:[\s\S]{0,140}?max_length\s*=\s*(\d+)',text,'description max_length').group(1) or need(r'description\s*:[\s\S]{0,140}?max_length\s*=\s*(\d+)',text,'description max_length').group(1))
price_min=float(need(r'price\s*:\s*float\s*=\s*Field\(gt\s*=\s*([0-9.]+)',text,'price minimum').group(1))
s=schemas['body_field_constraints.py'];op=s['paths']['/items/{item_id}']['put'];pars={p['name']:p for p in op['parameters']};props=s['components']['schemas']['Item']['properties'];db=str_branch(props['description'])
ok1,_=role_result('path','item_id',pars['item_id']); ok2='requestBody' in op
add('body_field_constraints','source-role accuracy',True,'PASS' if ok1 and ok2 else 'FAIL',f"source expects item_id/path and Item/requestBody; OpenAPI item_id={pars['item_id']['in']}; requestBody={ok2}.")
ok=db.get('maxLength')==desc_max and props['price'].get('exclusiveMinimum')==price_min and runtime['body_field_constraints.py']['price_fail']==422 and runtime['body_field_constraints.py']['description_fail']==422
add('body_field_constraints','condition disclosure',True,'PASS' if ok else 'FAIL',f"source description maxLength={desc_max}, price>{price_min}; OpenAPI maxLength={db.get('maxLength')}, exclusiveMinimum={props['price'].get('exclusiveMinimum')}; invalid requests=422/422.",'Declarative field constraints are used as the external condition representation.')
add('body_field_constraints','representation-disagreement preservation',False,'N/A','No unresolved explicit representation conflict exists in this official example.')
add('body_field_constraints','review-authority consistency',False,'N/A','No human review state exists in this official example.')

# Operation method/path role.
text=src('deprecated_operation.py')
expected_routes=re.findall(r'@app\.get\([\"\']([^\"\']+)[\"\']',text)
s=schemas['deprecated_operation.py'];paths=s['paths'];ok=set(expected_routes)=={'/items/','/users/','/elements/'} and all('get' in paths.get(p,{}) for p in expected_routes)
add('deprecated_operation','source-role accuracy',True,'PASS' if ok else 'FAIL',f"source GET routes={sorted(expected_routes)}; OpenAPI GET routes={sorted(p for p in expected_routes if 'get' in paths.get(p,{}))}.")
add('deprecated_operation','condition disclosure',False,'N/A','No explicit validation constraint is declared in these operations.')
add('deprecated_operation','representation-disagreement preservation',False,'N/A','No unresolved explicit representation conflict exists in this official example.')
add('deprecated_operation','review-authority consistency',False,'N/A','No human review state exists in this official example.')

status=[
 {'example':'query_param_constraints','source_status':'Query(deprecated=True)','published_status':str(schemas['query_param_constraints.py']['paths']['/items/']['get']['parameters'][0].get('deprecated')),'outcome':'PASS' if schemas['query_param_constraints.py']['paths']['/items/']['get']['parameters'][0].get('deprecated') is True else 'FAIL'},
 {'example':'deprecated_operation','source_status':'@app.get(..., deprecated=True)','published_status':str(paths['/elements/']['get'].get('deprecated')),'outcome':'PASS' if paths['/elements/']['get'].get('deprecated') is True else 'FAIL'},
]

# Negative controls against the exact role comparator. These are not part of the seven
# external outcomes; they validate that role/name substitutions are rejected.
q_bad_location=copy.deepcopy(q); q_bad_location['in']='header'
q_bad_name=copy.deepcopy(q); q_bad_name['name']='wrong-parameter'
neg=[]
for name,obj in [('wrong_location',q_bad_location),('wrong_name',q_bad_name)]:
    ok,reason=role_result('query',alias,obj)
    neg.append({'control':name,'expected':'FAIL','observed':'PASS' if ok else 'FAIL','reason':reason})
if any(x['observed']!='FAIL' for x in neg): raise SystemExit(f'external role negative control failed: {neg}')
(AUD/'external_role_negative_controls.json').write_text(json.dumps(neg,indent=2)+'\n')

with open(AUD/'external_direct_checklist.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
with open(AUD/'status_propagation_analogue.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=status[0].keys());w.writeheader();w.writerows(status)
summary={'upstream_repository':'fastapi/fastapi','upstream_commit':UPSTREAM_COMMIT,'fastapi_version':fastapi.__version__,'pydantic_version':pydantic.__version__,'source_provenance':provenance,'generated_sha256':{p.name:sha256(p) for p in sorted(GEN.glob('*.json'))},'runtime':runtime,'direct_cells':len(rows),'direct_applicable':sum(r['applicable']=='True' for r in rows),'direct_pass':sum(r['outcome']=='PASS' for r in rows),'direct_fail':sum(r['outcome']=='FAIL' for r in rows),'direct_na':sum(r['outcome']=='N/A' for r in rows),'status_analogue_pass':sum(r['outcome']=='PASS' for r in status),'status_analogue_total':len(status),'role_negative_controls':neg}
(AUD/'external_transfer_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if not (summary['direct_applicable']==7 and summary['direct_pass']==7 and summary['direct_fail']==0 and summary['direct_na']==9 and summary['status_analogue_pass']==2):
    raise SystemExit(f'unexpected external transfer summary: {summary}')
print(json.dumps(summary,indent=2))
