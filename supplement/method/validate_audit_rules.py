"""Controlled positive/negative controls for the released Paper 2 audit rules.

These fixtures test the checker implementation, not population accuracy. Expected outcomes
are written explicitly in the fixture table and are independent of the functions under test.
"""
from __future__ import annotations
import csv, json
from pathlib import Path
from audit_rules import (
    authority_consistency_check,
    comment_role_defect,
    compare_published_role,
    conflict_routing_check,
    guard_semantics_check,
)

HERE = Path(__file__).resolve().parent
OUT_CSV = HERE / "CHECKER_VALIDATION_CASES.csv"
OUT_JSON = HERE / "CHECKER_VALIDATION_RESULT.json"
EXEC_PREFIXES = (
    "Output alias:", "Calculation expression:", "Scope boundary:", "Query entry point:",
    "Package boundary:", "KPI function:", "Source relation:", "Execution delimiter:", "Return contract:"
)

cases=[]
def record(name, family, expected, observed, detail):
    cases.append({"case":name,"family":family,"expected":expected,"observed":observed,"matched":expected==observed,"detail":detail})

# Source-role positive and negative controls.
ok,why=compare_published_role("query","item-query","query","item-query")
record("role_correct","source_role","PASS","PASS" if ok else "FAIL",why)
ok,why=compare_published_role("query","item-query","header","item-query")
record("role_wrong_location","source_role","FAIL","PASS" if ok else "FAIL",why)
ok,why=compare_published_role("query","item-query","query","wrong-parameter")
record("role_wrong_name","source_role","FAIL","PASS" if ok else "FAIL",why)
record("lineage_comment_benign","source_role","PASS","FAIL" if comment_role_defect('# KPI: Throughput','Source context: supports the KPI definition.',EXEC_PREFIXES) else "PASS","benign comment assigned a non-executable role")
record("lineage_comment_as_alias","source_role","FAIL","FAIL" if comment_role_defect('"""Calculates yield."""','Output alias: maps this expression to a in the result set.',EXEC_PREFIXES) else "PASS","docstring assigned executable output-alias role")

# Guard binding/semantics controls.
def gv(name, expected, variable, kind, denominator, text):
    ok,why=guard_semantics_check(variable,kind,denominator,text)
    record(name,"condition_disclosure",expected,"PASS" if ok else "FAIL",why)

gv("guard_zero_correct","PASS","hours_online","zero","Hours Online","Implementation logic checks for a zero denominator before returning the KPI value.")
gv("guard_missing_denominator","FAIL","hours_online","zero","","Implementation logic checks for a zero denominator before returning the KPI value.")
gv("guard_wrong_denominator","FAIL","cost","zero","Revenue","Implementation logic checks for a zero denominator before returning the KPI value.")
gv("guard_contradictory_text","FAIL","hours_online","zero","Hours Online","No zero handling is provided.")
gv("guard_disabled_text","FAIL","hours_online","zero","Hours Online","The zero guard is disabled.")
gv("guard_nonpositive_correct","PASS","feedstock_input_tons","nonpositive","Feedstock Input (Tons)","If the denominator is non-positive (<= 0), the implementation returns 0 before division.")
gv("guard_nonpositive_reduced_to_zero","FAIL","feedstock_input_tons","nonpositive","Feedstock Input (Tons)","Implementation logic checks for a zero denominator before returning the KPI value.")

# Conflict routing and authority-language controls.
record("conflict_routing_correct","conflict_routing","PASS",conflict_routing_check(True,"Needs Review",True),"explicit conflict remains routed to Needs Review and Review Queue")
record("conflict_routing_suppressed","conflict_routing","FAIL",conflict_routing_check(True,"Needs Review",False),"Review Queue removed from an explicit conflict")
record("conflict_not_applicable","conflict_routing","N/A",conflict_routing_check(False,"Validated",False),"benign non-conflict control")
record("authority_unresolved_clean","review_authority","PASS",authority_consistency_check("Needs Review",[]),"unresolved page without certification wording")
record("authority_unresolved_certified","review_authority","FAIL",authority_consistency_check("Needs Review",["Print Certified Dossier"]),"certification wording beside unresolved status")
record("authority_validated_control","review_authority","N/A",authority_consistency_check("Validated",["Print Certified Dossier"]),"resolved-status benign applicability control")

with OUT_CSV.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(cases[0])); w.writeheader(); w.writerows(cases)

mismatches=[c for c in cases if not c['matched']]
# For binary PASS/FAIL cases, report conventional false-alarm/miss counts against explicit fixture truth.
binary=[c for c in cases if c['expected'] in {'PASS','FAIL'}]
false_positives=sum(c['expected']=='PASS' and c['observed']=='FAIL' for c in binary)
false_negatives=sum(c['expected']=='FAIL' and c['observed']=='PASS' for c in binary)
summary={
    "fixture_cases":len(cases),
    "binary_cases":len(binary),
    "matched":len(cases)-len(mismatches),
    "mismatched":len(mismatches),
    "false_alarms_on_benign_controls":false_positives,
    "misses_on_defect_controls":false_negatives,
    "all_expected_outcomes_matched":not mismatches,
    "interpretation":"Controlled checker-validation fixtures only; not an empirical estimate of defect prevalence or checker accuracy in a population.",
    "cases":cases,
}
OUT_JSON.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
if mismatches:
    raise SystemExit(f"checker validation mismatches: {mismatches}")
