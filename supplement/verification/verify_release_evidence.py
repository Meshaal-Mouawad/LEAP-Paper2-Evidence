from pathlib import Path
import csv,hashlib,json,re,subprocess,tempfile,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def ck(name,ok,detail=None):checks.append({'name':name,'passed':bool(ok),'detail':detail})
# Manifest integrity
manifest=ROOT/'SHA256SUMS.txt'; bad=[]; n=0
for line in manifest.read_text().splitlines():
    h,rel=line.split(None,1);p=ROOT/rel.strip();n+=1
    if not p.is_file() or sha(p)!=h:bad.append(rel.strip())
ck('supplement_manifest',not bad,{'entries':n,'bad':bad})
# Checker validation
v=json.loads((ROOT/'method/CHECKER_VALIDATION_RESULT.json').read_text())
m=json.loads((ROOT/'method/MUTATED_ARTIFACT_VALIDATION_RESULT.json').read_text())
ck('checker_rule_fixtures',v['fixture_cases']==18 and v['matched']==18 and v['mismatched']==0 and v['false_alarms_on_benign_controls']==0 and v['misses_on_defect_controls']==0,v)
ck('checker_artifact_derived_controls',m['cases']==14 and m['matched']==14 and m['mismatched']==0 and m['false_alarms_on_benign_controls']==0 and m['misses_on_defect_controls']==0,m)
o=json.loads((ROOT/'method/CONTROL_ORACLE_VERIFICATION_RESULT.json').read_text())
ck('checker_control_oracles',o['status']=='PASS' and all(x['passed'] for x in o['checks']),o)
heading=[x for x in m.get('details',[]) if x.get('case')=='actual_guard_heading_only_document_mutation']
ck('checker_heading_only_reparse',len(heading)==1 and heading[0].get('expected')=='FAIL' and heading[0].get('observed')=='FAIL',heading)
# External repaired role negative controls
e=json.loads((ROOT/'external_fastapi/audit/external_transfer_summary.json').read_text())
neg=e.get('role_negative_controls',[])
ck('external_role_negative_controls',len(neg)==2 and all(x.get('expected')=='FAIL' and x.get('observed')=='FAIL' for x in neg),neg)
# Primary summaries
p=json.loads((ROOT/'primary/audit/audit_summary_r3.json').read_text())
ck('primary_corpus',p['corpus']['dossiers']==28 and p['corpus']['needs_review']==19 and p['corpus']['validated']==9,p['corpus'])
ck('primary_defect_classes',p['defect_classes']['lineage_typing']['affected_dossiers']==4 and p['defect_classes']['lineage_typing']['visible_instances']==12 and p['defect_classes']['guard_to_safeguard_binding']['guard_instances']==10 and p['defect_classes']['guard_to_safeguard_binding']['failure_instances']==5 and p['defect_classes']['authority_language_template']['affected_dossiers']==19)
ck('primary_working_mechanism',p['working_mechanism']['conflict_routing']['eligible_explicit_conflict_dossiers']==6 and p['working_mechanism']['conflict_routing']['preserved_dossiers']==6)
# Guard CSV is complete and deterministic
rows=list(csv.DictReader((ROOT/'primary/audit/guard_audit_10_r3.csv').open()))
ck('primary_guard_inventory',len(rows)==10 and sum(r['verdict']=='failure' for r in rows)==5 and sum(r['verdict']=='preserved' for r in rows)==5)
# Historical
h=json.loads((ROOT/'historical/audit/historical_summary.json').read_text())
ck('historical_corpus',h['dossiers']==18 and h['needs_review']==12 and h['validated']==6,h)
ck('historical_defects',h['lineage']=={'affected_dossiers':4,'instances':12} and h['guards']=={'instances':9,'failures':4,'preserved':5} and h['authority']=={'eligible':12,'affected':12})
ck('historical_conflict_routing',h['conflict_routing']=={'eligible':6,'preserved':6})
# Robustness configurations
s=json.loads((ROOT/'robustness/audit/scenarios_summary.json').read_text());c=json.loads((ROOT/'robustness/audit/challenge_summary.json').read_text())
ck('scenario_build',s['dossiers']==29 and s['status']=={'needs_review':11,'validated':18} and s['lineage_typing']['affected_dossiers']==1 and s['authority_language']=={'eligible_needs_review':11,'affected_dossiers':11} and s['guard_binding']['preserved_instances']==1 and s['guard_binding']['failure_instances']==0)
ck('challenge_build',c['dossiers']==8 and c['status']=={'needs_review':6,'validated':2} and c['lineage_typing']['affected_dossiers']==1 and c['authority_language']=={'eligible_needs_review':6,'affected_dossiers':6} and c['guard_binding']['preserved_instances']==1 and c['guard_binding']['failure_instances']==0)
# Primary public artifact identity
pub=json.loads((ROOT/'primary/artifact_28/PUBLIC_ARTIFACT_HASH_VERIFICATION.json').read_text())
ck('public_primary_identity',pub['status']=='PASS' and pub['matched']==28 and pub['total']==28)
# Root-cause trace contains expected source patterns
rc=(ROOT/'primary/audit/ROOT_CAUSE_SOURCE_EXCERPTS.txt').read_text()
for name,needle in [('lineage_comment_order','calculation|formula'),('lineage_comment_prefix','clean.startswith(("--", "#", "//", "\'"))'),('alias_rule','Output alias: maps this expression'),('guard_nullif','NULLIF'),('guard_eq_zero','==\\s*0'),('certified_formula','certified calculation expression'),('certify_definition','LEAP certifies the KPI definition'),('print_certified','Print Certified Dossier')]:
    ck('root_cause_'+name,needle in rc)
# No human adjudication file remains in R3 release
names=[p.name for p in ROOT.rglob('*') if p.is_file()]
ck('no_manual_condition_adjudication',not any('condition_adjudication' in x.lower() for x in names))
# Exact authorship/AI scope is outside supplement but no Bryan in supplement
text='\n'.join(p.read_text(errors='ignore') for p in ROOT.rglob('*') if p.is_file() and p.suffix.lower() in {'.md','.txt','.csv','.json','.py'})
ck('no_bryan_in_evidence',not re.search(r'Bryan A\. Jones|B\.A\. Jones',text,re.I))
result={'status':'PASS' if all(x['passed'] for x in checks) else 'FAIL','passed':sum(x['passed'] for x in checks),'total':len(checks),'checks':checks}
print(json.dumps(result,indent=2));sys.exit(0 if result['status']=='PASS' else 1)
