"""Artifact-derived checker validation using released LEAP/FastAPI evidence.

The expected outcomes are explicit in this file and are not inferred from checker output.
The 14 controls comprise five unchanged baselines, eight substitutions of extracted
inputs, and one document-level HTML mutation reparsed through the production adapter.
Frozen evidence files are never modified on disk.
"""
from __future__ import annotations
import csv, json, re, sys
from pathlib import Path
from bs4 import BeautifulSoup
from audit_rules import (
    authority_consistency_check, comment_role_defect, compare_published_role,
    conflict_routing_check, guard_semantics_check,
)

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PRIMARY=ROOT/'primary'/'artifact_28'/'dossiers'
EXT=ROOT/'external_fastapi'
OUT_CSV=HERE/'MUTATED_ARTIFACT_CONTROLS.csv'
OUT_JSON=HERE/'MUTATED_ARTIFACT_VALIDATION_RESULT.json'
EXEC_PREFIXES=(
    'Output alias:','Calculation expression:','Scope boundary:','Query entry point:',
    'Package boundary:','KPI function:','Source relation:','Execution delimiter:','Return contract:'
)
CERT=['Certified metric dossier','certified formula','certifies the KPI definition','certified calculation expression','Print Certified Dossier','certified implementation path']

cases=[]
def rec(name,family,expected,observed,detail):
    cases.append({'case':name,'family':family,'expected':expected,'observed':observed,'matched':expected==observed,'detail':detail})

def xs_from_html(html):
    soup=BeautifulSoup(html,'html.parser')
    return [x.strip() for x in soup.stripped_strings]

def xs_for(name):
    return xs_from_html((PRIMARY/name).read_text(errors='ignore'))
def after(xs,label):
    for i,x in enumerate(xs[:-1]):
        if x==label:return xs[i+1]
    return ''

# Actual LEAP guard page: retain the valid baseline, test three extracted-input
# substitutions, then perform one document-level mutation and reparse it through
# the same BeautifulSoup/stripped_strings production adapter used above.
guard_path=PRIMARY/'daily_feedstock_throughput_tonsday.html'
guard_html=guard_path.read_text(errors='ignore')
xs=xs_from_html(guard_html)
den=after(xs,'Denominator:'); safe=after(xs,'Zero-Division Guard:')
for name,expected,d,t in [
    ('actual_guard_baseline','PASS',den,safe),
    ('actual_guard_missing_denominator','FAIL','',safe),
    ('actual_guard_wrong_denominator','FAIL','Revenue',safe),
    ('actual_guard_contradictory_safeguard','FAIL',den,'No zero handling is provided.'),
]:
    ok,why=guard_semantics_check('hours_online','zero',d,t)
    rec(name,'condition_disclosure',expected,'PASS' if ok else 'FAIL',why)

original_sentence='Implementation logic checks for a zero denominator before returning the KPI value.'
if original_sentence not in guard_html:
    raise SystemExit('guard explanatory sentence not found for document-level mutation')
mutated_html=guard_html.replace(original_sentence,'Zero-Division Guard:',1)
mutated_xs=xs_from_html(mutated_html)
mutated_den=after(mutated_xs,'Denominator:')
mutated_safe=after(mutated_xs,'Zero-Division Guard:')
ok,why=guard_semantics_check('hours_online','zero',mutated_den,mutated_safe)
rec('actual_guard_heading_only_document_mutation','condition_disclosure','FAIL','PASS' if ok else 'FAIL',
    f'reparsed HTML safeguard={mutated_safe!r}; {why}')

# Actual Yield lineage pair: preserve the source docstring and mutate only its published role label.
xs=xs_for('ethylene_production_yield.html')
raw=''; desc=''
for i,x in enumerate(xs[:-1]):
    if 'Calculates ethylene production yield as a percentage of feedstock input.' in x:
        raw=re.sub(r'^\d+\s*\|\s*','',x).strip(); desc=xs[i+1]; break
if not raw: raise SystemExit('yield docstring pair not found')
defect=comment_role_defect(raw,desc,EXEC_PREFIXES)
rec('actual_yield_lineage_defect','source_role','FAIL','FAIL' if defect else 'PASS',desc)
benign='Source context: supports the KPI definition or execution boundary.'
defect=comment_role_defect(raw,benign,EXEC_PREFIXES)
rec('actual_yield_lineage_benign_label','source_role','PASS','FAIL' if defect else 'PASS',benign)

# Actual Gross Margin conflict and authority page: suppress routing / certification in memory.
xs=xs_for('gross_margin_percentage.html'); full='\n'.join(xs)
status='Needs Review' if 'Needs Review' in xs else 'Unknown'
rec('actual_conflict_routing_baseline','conflict_routing','PASS',conflict_routing_check(True,status,'Review Queue' in xs),'actual page includes Needs Review and Review Queue')
rec('actual_conflict_routing_suppressed','conflict_routing','FAIL',conflict_routing_check(True,status,False),'in-memory negative control removes Review Queue')
cert=[c for c in CERT if c.lower() in full.lower()]
rec('actual_authority_certification_defect','review_authority','FAIL',authority_consistency_check(status,cert),f'certification phrases={cert}')
rec('actual_authority_benign_control','review_authority','PASS',authority_consistency_check(status,[]),'in-memory benign control removes certification wording while retaining Needs Review')

# Actual external query OpenAPI: baseline then wrong role/name mutations.
schema=json.loads((EXT/'generated'/'query_param_constraints.openapi.json').read_text())
q=schema['paths']['/items/']['get']['parameters'][0]
source=(EXT/'source'/'query_param_constraints.py').read_text()
m=re.search(r'alias\s*=\s*[\"\']([^\"\']+)',source)
if not m: raise SystemExit('source query alias not found')
alias=m.group(1)
for name,expected,loc,pname in [
    ('actual_external_role_baseline','PASS',q.get('in',''),q.get('name','')),
    ('actual_external_role_wrong_location','FAIL','header',q.get('name','')),
    ('actual_external_role_wrong_name','FAIL',q.get('in',''),'wrong-parameter'),
]:
    ok,why=compare_published_role('query',alias,loc,pname)
    rec(name,'external_source_role',expected,'PASS' if ok else 'FAIL',why)

with OUT_CSV.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
mis=[c for c in cases if not c['matched']]
binary=[c for c in cases if c['expected'] in {'PASS','FAIL'}]
fp=sum(c['expected']=='PASS' and c['observed']=='FAIL' for c in binary)
fn=sum(c['expected']=='FAIL' and c['observed']=='PASS' for c in binary)
report={
    'cases':len(cases),'matched':len(cases)-len(mis),'mismatched':len(mis),
    'false_alarms_on_benign_controls':fp,'misses_on_defect_controls':fn,
    'all_expected_outcomes_matched':not mis,
    'interpretation':'Artifact-derived controls validate the released checker on specified archived baselines/substitutions plus one reparsed document mutation; they do not estimate population-level sensitivity or specificity.',
    'details':cases,
}
OUT_JSON.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if mis: raise SystemExit(f'mutated artifact control mismatches: {mis}')
