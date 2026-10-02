from pathlib import Path
import csv,json
HERE=Path(__file__).resolve().parent

def load(name):
    with (HERE/name).open(newline="") as f:return {r["case"]:r for r in csv.DictReader(f)}

def check(oracle_name, output_name):
    oracle=load(oracle_name); output=load(output_name)
    missing=sorted(set(oracle)-set(output)); extra=sorted(set(output)-set(oracle)); mismatches=[]
    for case,row in oracle.items():
        if case in output and output[case].get("observed") != row["expected"]:
            mismatches.append({"case":case,"oracle_expected":row["expected"],"observed":output[case].get("observed")})
    return {"oracle":oracle_name,"output":output_name,"oracle_cases":len(oracle),"missing":missing,"extra":extra,"mismatches":mismatches,"passed":not missing and not extra and not mismatches}

checks=[check("CHECKER_CONTROL_ORACLE.csv","CHECKER_VALIDATION_CASES.csv"),check("ARTIFACT_MUTATION_ORACLE.csv","MUTATED_ARTIFACT_CONTROLS.csv")]
report={"status":"PASS" if all(x["passed"] for x in checks) else "FAIL","checks":checks,"interpretation":"Control labels are read from predeclared oracle tables separate from the released checker output."}
(HERE/"CONTROL_ORACLE_VERIFICATION_RESULT.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
if report["status"] != "PASS":raise SystemExit(1)
