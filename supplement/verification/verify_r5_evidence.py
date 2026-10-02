from pathlib import Path
import csv, json, sys
ROOT=Path(__file__).resolve().parents[1]

def j(p): return json.loads((ROOT/p).read_text())
def rows(p): return list(csv.DictReader(open(ROOT/p,newline='')))
checks=[]
def ck(name,cond,detail=''): checks.append({'check':name,'passed':bool(cond),'detail':detail})

# Checker validation gates
v=j('method/CHECKER_VALIDATION_RESULT.json')
m=j('method/MUTATED_ARTIFACT_VALIDATION_RESULT.json')
ck('rule fixtures 18/18',v['fixture_cases']==18 and v['matched']==18 and v['mismatched']==0,str({k:v[k] for k in ['fixture_cases','matched','mismatched']}))
ck('rule fixtures zero misses/false alarms',v['false_alarms_on_benign_controls']==0 and v['misses_on_defect_controls']==0)
ck('artifact-derived controls 14/14',m['cases']==14 and m['matched']==14 and m['mismatched']==0,str({k:m[k] for k in ['cases','matched','mismatched']}))
ck('artifact-derived controls zero misses/false alarms',m['false_alarms_on_benign_controls']==0 and m['misses_on_defect_controls']==0)
o=j('method/CONTROL_ORACLE_VERIFICATION_RESULT.json')
ck('predeclared control oracles',o['status']=='PASS' and all(x['passed'] for x in o['checks']),str(o))
heading=[x for x in m.get('details',[]) if x.get('case')=='actual_guard_heading_only_document_mutation']
ck('heading-only production-adapter regression',len(heading)==1 and heading[0]['expected']=='FAIL' and heading[0]['observed']=='FAIL',heading)

p=j('primary/audit/audit_summary_r3.json')
h=j('historical/audit/historical_summary.json')
s=j('robustness/audit/scenarios_summary.json')
c=j('robustness/audit/challenge_summary.json')
e=j('external_fastapi/audit/external_transfer_summary.json')

ck('primary 28 dossiers',p['corpus']['dossiers']==28,str(p.get('corpus')))
ck('primary three defect classes',len(p['defect_classes'])==3 and all(v.get('class_count')==1 for v in p['defect_classes'].values()),str(p['defect_classes']))
ck('primary guard 5 fail 5 preserve',p['defect_classes']['guard_to_safeguard_binding']['guard_instances']==10 and p['defect_classes']['guard_to_safeguard_binding']['failure_instances']==5 and p['defect_classes']['guard_to_safeguard_binding']['preserved_instances']==5)
ck('primary conflict mechanism 6/6',p['working_mechanism']['conflict_routing']['eligible_explicit_conflict_dossiers']==6 and p['working_mechanism']['conflict_routing']['preserved_dossiers']==6)
ck('historical 18 dossiers',h['dossiers']==18)
ck('historical lineage 4/12',h['lineage']=={'affected_dossiers':4,'instances':12})
ck('historical guard 4 fail 5 preserve',h['guards']['instances']==9 and h['guards']['failures']==4 and h['guards']['preserved']==5)
ck('historical authority 12/12',h['authority']['eligible']==12 and h['authority']['affected']==12)
ck('historical conflict 6/6',h['conflict_routing']['eligible']==6 and h['conflict_routing']['preserved']==6)

pr=rows('primary/audit/dossier_audit_28_r3.csv'); hr=rows('historical/audit/historical_dossiers.csv')
pl={r['dossier'] for r in pr if r['lineage_typing_defect']=='True'}; hl={r['dossier'] for r in hr if r['lineage_defect']=='True'}
pc={r['dossier'] for r in pr if r['explicit_conflict']=='True'}; hc={r['dossier'] for r in hr if r['explicit_conflict']=='True'}
ck('same four lineage dossiers across LEAP states',pl==hl and len(pl)==4,sorted(pl))
ck('same six conflict dossiers across LEAP states',pc==hc and len(pc)==6,sorted(pc))
ck('scenario reproduces lineage+authority not guard',s['lineage_typing']['affected_dossiers']==1 and s['authority_language']['affected_dossiers']==11 and s['guard_binding']['failure_instances']==0,str(s))
ck('challenge reproduces lineage+authority not guard',c['lineage_typing']['affected_dossiers']==1 and c['authority_language']['affected_dossiers']==6 and c['guard_binding']['failure_instances']==0,str(c))

ck('external source blobs verified',all(x['blob_match'] for x in j('external_fastapi/audit/SOURCE_PROVENANCE.json')['files'].values()))
ck('external direct 7/7',e['direct_applicable']==7 and e['direct_pass']==7 and e['direct_fail']==0,str({k:e[k] for k in ['direct_applicable','direct_pass','direct_fail']}))
ck('external nine N/A',e['direct_na']==9)
ck('external status analogues 2/2',e['status_analogue_pass']==2 and e['status_analogue_total']==2)
neg=e.get('role_negative_controls',[])
ck('external wrong-role/name controls rejected',len(neg)==2 and all(x['expected']=='FAIL' and x['observed']=='FAIL' for x in neg),neg)
rt=e['runtime']
ck('external invalid query constraints return 422',rt['query_param_constraints.py']['too_short']==422 and rt['query_param_constraints.py']['pattern_fail']==422)
ck('external invalid numeric constraints return 422',rt['path_numeric_constraints.py']['path_low']==422 and rt['path_numeric_constraints.py']['size_high']==422)
ck('external invalid body constraints return 422',rt['body_field_constraints.py']['price_fail']==422 and rt['body_field_constraints.py']['description_fail']==422)

report={'passed':sum(x['passed'] for x in checks),'total':len(checks),'all_passed':all(x['passed'] for x in checks),'checks':checks}
(ROOT/'verification'/'R5_VERIFICATION_RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if not report['all_passed']: raise SystemExit(1)
