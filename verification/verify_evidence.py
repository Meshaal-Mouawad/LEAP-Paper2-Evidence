#!/usr/bin/env python3
"""Reproduce LEAP Paper 2 archived-evidence checks without executing the archived KPI code.

Run from an extracted R2 package:
    python verification/verify_evidence.py --root .
Optional original-archive comparison:
    python verification/verify_evidence.py --root . --source-archive '/path/JSS_Submtion 2.zip'

Dependencies: Python 3.10+ and SymPy. No network or model service is used.
"""
from __future__ import annotations
import argparse
import ast
import csv
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys
import zipfile

try:
    import sympy as sp
except ImportError as exc:
    raise SystemExit('Install the supplied requirements: python -m pip install -r verification/requirements.txt') from exc


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding='utf-8-sig', newline='') as fh:
        return list(csv.DictReader(fh))


def sym_expression(node: ast.AST, names: dict[str, sp.Symbol]) -> sp.Expr:
    """Convert only the arithmetic syntax used by the preserved formula to symbolic form."""
    if isinstance(node, ast.Name) and node.id.lower() in names:
        return names[node.id.lower()]
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return sp.Rational(str(node.value))
    if isinstance(node, ast.BinOp):
        a, b = sym_expression(node.left, names), sym_expression(node.right, names)
        if isinstance(node.op, ast.Add): return a + b
        if isinstance(node.op, ast.Sub): return a - b
        if isinstance(node.op, ast.Mult): return a * b
        if isinstance(node.op, ast.Div): return a / b
        if isinstance(node.op, ast.Pow): return a ** b
    raise ValueError(f'Unsupported expression node: {ast.dump(node)}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source-archive', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    supplement = root / 'evidence/supplement'
    cases = root / 'evidence/cases'
    results: dict = {
        'purpose': 'Reproduction of retained evidence and reported calculations; not a new experiment or independent survey collection.',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'python_version': sys.version.split()[0],
        'sympy_version': sp.__version__,
        'checks': [],
        'interpretation_limits': [
            'Survey checks reproduce the supplied category counts and profile, not a complete original respondent-by-item dataset.',
            'Meeting checks authenticate arithmetic within the supplied log, not whether start/end fields were observed or scheduled.',
            'The positive-domain bound is a symbolic statement over real positive revenue and cost.',
            'No archived KPI function is executed; source evidence is parsed as data.'
        ]
    }

    def check(name: str, condition: bool, details=None) -> None:
        record = {'name': name, 'passed': bool(condition)}
        if details is not None: record['details'] = details
        results['checks'].append(record)
        if not condition:
            raise AssertionError(name)

    # All three reported distributions and both profile distributions use N=60.
    survey = csv_rows(supplement / 'survey_counts_N60.csv')
    grouped: dict[str, dict[str, int]] = defaultdict(dict)
    for row in survey:
        check('survey row denominator: ' + row['Item'] + '/' + row['Category'], int(row['N']) == 60)
        count = int(row['Count'])
        check('survey count nonnegative: ' + row['Category'], count >= 0)
        grouped[row['Item']][row['Category']] = count
    expected = {
        'Misinterpretation frequency': {'Daily':16,'Weekly':26,'Monthly':18,'Rarely':0,'Never':0},
        'Expected error reduction': {'Yes, significantly':30,'Slightly':11,'No change':6,'Unsure':13},
        'Expected time saved': {'Less than 1 hour':18,'1–4 hours':11,'5–8 hours':28,'1 day or more':3},
    }
    check('all three N60 distributions match the manuscript', dict(grouped) == expected)
    check('all three distributions total 60', all(sum(c.values()) == 60 for c in grouped.values()))
    results['survey'] = {
        'N':60,
        'items':dict(grouped),
        'percentages':{item:{label:count / 60 * 100 for label,count in counts.items()} for item,counts in grouped.items()},
        'daily_or_weekly':{'count':42,'percentage':42/60*100},
        'some_expected_error_reduction':{'count':41,'percentage':41/60*100},
        'at_least_five_hours_expected':{'count':31,'percentage':31/60*100}
    }
    profile: dict[str, dict[str, int]] = defaultdict(dict)
    for row in csv_rows(supplement / 'survey_profile_N60.csv'):
        check('profile denominator: '+row['Category'], int(row['N']) == 60)
        profile[row['Variable']][row['Category']] = int(row['Count'])
    check('role and experience totals', len(profile)==2 and all(sum(d.values())==60 for d in profile.values()))
    check('role counts', profile['Role']=={'Developer':51,'Executive':3,'Project Manager':3,'Business Analyst':1,'AI Governance Consultant':1,'Quality Manager':1})
    check('experience counts', profile['Enterprise-system experience']=={'<1 year':7,'1-3 years':22,'4-6 years':9,'7+ years':22})
    results['survey_profile'] = dict(profile)

    # Calculate every time interval and phase summary directly from the retained log.
    meetings = csv_rows(supplement / 'meeting_duration_log.csv')
    check('60 included records',len(meetings)==60)
    dates=[]
    durations=[]
    by_phase: dict[str, list[dict]] = defaultdict(list)
    for n, row in enumerate(meetings, start=1):
        date=datetime.strptime(row['Date'],'%Y-%m-%d').date()
        a=datetime.strptime(row['Start Time KSA'],'%H:%M')
        b=datetime.strptime(row['End Time KSA'],'%H:%M')
        duration=(b-a).total_seconds()/60
        check(f'meeting {n}: identifier, weekday, status, timezone',int(row['Meeting No'])==n and row['Day']=='Tuesday' and date.weekday()==1 and row['Status']=='Completed' and row['Timezone']=='Asia/Riyadh UTC+3')
        check(f'meeting {n}: end minus start', duration==float(row['Duration Minutes']) and duration>=0)
        check(f'meeting {n}: archived hours rounded to two decimals', round(duration/60,2)==float(row['Duration Hours']))
        dates.append(date); durations.append(duration); by_phase[row['Phase']].append(row)
    check('59 consecutive seven-day intervals', all((b-a).days==7 for a,b in zip(dates,dates[1:])))
    check('meeting date endpoints', dates[0].isoformat()=='2025-02-04' and dates[-1].isoformat()=='2026-03-24')
    summaries=[]
    for phase, rows in by_phase.items():
        values=[float(r['Duration Minutes']) for r in rows]
        summaries.append({'phase':phase,'n':len(values),'total_minutes':sum(values),'mean':statistics.mean(values),'median':statistics.median(values),'min':min(values),'max':max(values),'sample_sd':statistics.stdev(values),'above_40':sum(v>40 for v in values)})
    check('phase counts 11,5,27,17',[s['n'] for s in summaries]==[11,5,27,17])
    check('phase totals 660,237,1020,580',[s['total_minutes'] for s in summaries]==[660,237,1020,580])
    check('Table 2 displayed means',[round(s['mean'],1) for s in summaries]==[60.0,47.4,37.8,34.1])
    check('Table 2 sample SDs',[round(s['sample_sd'],2) for s in summaries]==[0.00,2.51,9.13,3.52])
    check('Table 2 medians',[s['median'] for s in summaries]==[60,47,30,35])
    for row in csv_rows(supplement/'meeting_phase_definition.csv'):
        phase_rows=by_phase[row['Archived_phase_label']]
        check('phase definition '+row['Archived_phase_label'],
              int(row['N'])==len(phase_rows) and row['Meeting_first']==phase_rows[0]['Meeting No'] and row['Meeting_last']==phase_rows[-1]['Meeting No'] and row['Date_first']==phase_rows[0]['Date'] and row['Date_last']==phase_rows[-1]['Date'])
    post=durations[11:]
    check('post-baseline 1837/49',len(post)==49 and sum(post)==1837 and statistics.mean(post)==1837/49)
    check('phase 3 above 40; phase 4 at most 40',summaries[2]['above_40']==11 and summaries[3]['above_40']==0)
    results['meetings']={'record_count':60,'phase_summaries':summaries,'post_baseline':{'n':49,'total_minutes':sum(post),'mean':statistics.mean(post),'percent_below_baseline':(1-statistics.mean(post)/60)*100},'phase4_percent_below_baseline':(1-summaries[3]['mean']/60)*100}

    # Authenticate raw case bytes against the supplied hash manifest and optional original ZIP.
    manifest=csv_rows(supplement/'case_evidence_manifest.csv')
    results['case_files']=[]
    original=None
    if args.source_archive:
        check('original archive exists',args.source_archive.is_file())
        check('original companion archive SHA256',sha256(args.source_archive)==manifest[0]['Source_archive_SHA256'])
        original=zipfile.ZipFile(args.source_archive)
    try:
        for row in manifest:
            f=cases/row['File']
            check('case file digest '+row['File'],sha256(f)==row['SHA256'] and f.stat().st_size==int(row['Bytes']))
            rec={'file':str(f.relative_to(root)),'sha256':sha256(f),'bytes':f.stat().st_size,'original_archive_comparison':'not requested'}
            if original is not None:
                check('case bytes match original archive '+row['File'], original.read(row['Archive_member'])==f.read_bytes())
                rec['original_archive_comparison']='byte-identical'
                rec['archive_member']=row['Archive_member']
            results['case_files'].append(rec)
    finally:
        if original is not None: original.close()

    # Parse Yield source and check the exact archived publication locations.
    yield_tree=ast.parse((cases/'control_no_conflict_yield.py').read_text())
    yield_fn=next(n for n in yield_tree.body if isinstance(n, ast.FunctionDef))
    check('Yield docstring identity', ast.get_docstring(yield_fn)=='Calculates ethylene production yield as a percentage of feedstock input.')
    guard=next(n for n in yield_fn.body if isinstance(n, ast.If))
    check('Yield non-positive-input guard',isinstance(guard.test,ast.Compare) and isinstance(guard.test.left,ast.Name) and guard.test.left.id=='feedstock_input_tons' and isinstance(guard.test.ops[0],ast.LtE) and ast.literal_eval(guard.test.comparators[0])==0 and isinstance(guard.body[0],ast.Return) and ast.literal_eval(guard.body[0].value)==0)
    yhtml=(cases/'ethylene_production_yield.html').read_text()
    yl=yhtml.splitlines()
    role='Output alias: maps this expression to a in the result set.'
    check('Yield role fault twice within one dossier',yhtml.count(role)==2 and role in yl[271] and role in yl[294])
    check('Yield Validated state', 'Validated' in yl[125] and 'Validated' in yl[130])
    check('Yield formal field and ratio locations','Formal Formula' in yl[232] and r'\frac{\mathrm{Ethylene\,Produced}}{\mathrm{Feedstock\,Input}}' in yl[234])
    check('Yield formula field lacks guard', all(token not in yl[234] for token in ('feedstock_input_tons','return 0','<=','&lt;=')))
    check('Yield source guard retained in dossier', 'feedstock_input_tons' in yl[286] and 'return 0.0' in yl[286])
    check('Yield formal field stated role', 'certified calculation expression' in yl[302] and 'formal MathJax formula shown above' in yl[302])

    # Algebra comes from parsed declaration and the actual ordinary return expression.
    margin_source=(cases/'conflict_formula_margin.py').read_text()
    mt=ast.parse(margin_source)
    mf=next(n for n in mt.body if isinstance(n,ast.FunctionDef))
    mg=next(n for n in mf.body if isinstance(n,ast.If))
    check('Margin cost-zero guard',isinstance(mg.test,ast.Compare) and isinstance(mg.test.left,ast.Name) and mg.test.left.id=='cost' and isinstance(mg.test.ops[0],ast.Eq) and ast.literal_eval(mg.test.comparators[0])==0 and ast.literal_eval(mg.body[0].value)==0)
    R,C=sp.symbols('R C',positive=True)
    names={'revenue':R,'cost':C}
    decl=next(line for line in margin_source.splitlines() if line.startswith('# Formula:')).split('=',1)[1].strip()
    D=sym_expression(ast.parse(decl,mode='eval').body,names)
    I=sym_expression(next(n for n in reversed(mf.body) if isinstance(n,ast.Return)).value,names)
    identity=sp.factor((I-D-100)*R*C)
    check('Margin exact identity',sp.expand(identity-100*(R-C)**2)==0)
    check('Margin equality at R=C',sp.simplify((I-D).subs(R,C))==100)
    check('Margin positive-revenue zero-cost declared result',sp.simplify(D.subs(C,0))==100)
    check('Margin zero-revenue positive-cost implemented ratio',sp.simplify(I.subs(R,0))==0)
    results['margin_algebra']={
        'declared_expression':str(D),'ordinary_implementation_expression':str(I),
        'exact_identity':'(I-D-100)*R*C = 100*(R-C)**2',
        'sign_argument':'For R>0 and C>0, R*C>0 and the real square (R-C)**2>=0; hence I-D>=100. Equality holds exactly when R=C.',
        'boundary_cases':[
            {'condition':'R>0,C=0','declared':100,'implementation':0,'basis':'source cost-zero guard'},
            {'condition':'R=0,C>0','declared':'undefined: denominator is zero','implementation':0,'basis':'ordinary source ratio'}]
    }
    mhtml=(cases/'gross_margin_percentage.html').read_text()
    for phrase in ('Needs Review','Verified Logic Mapping','certified calculation expression','Print Certified Dossier'):
        check('Margin publication wording '+phrase,phrase in mhtml)

    # Relative paths are verified in the final delivery layout.
    checked_paths=[]
    for note in supplement.glob('*.md'):
        for rel in re.findall(r'`(\.\./cases/[^`]+)`',note.read_text()):
            resolved=(note.parent/rel).resolve()
            check('relative case path '+note.name+':'+rel,resolved.is_file() and resolved.is_relative_to(root))
            checked_paths.append({'note':str(note.relative_to(root)),'path':rel})
    results['relative_case_paths']=checked_paths
    check('case path references were actually found',len(checked_paths)>0)
    source = root/'submission/main.tex'
    if source.exists():
        tex=source.read_text()
        check('minor wording retained: Gao defines',r'\citet{Gao2026ECK} defines' in tex)
        check('minor wording retained: descriptive human evidence','descriptive human problem evidence' in tex and 'source-aware human problem evidence' not in tex)
        check('minor wording retained: failure condition','Failure condition: publication' in tex)
        check('minor wording retained: prior review/certification juxtaposition','already reports the Yield guard, the Gross Margin declared/executable mismatch, and the visible juxtaposition' in tex)
    results['input_sha256']={str(p.relative_to(root)):sha256(p) for p in sorted(list(supplement.glob('*.csv'))+list(cases.glob('*.py'))+list(cases.glob('*.html')))}
    results['check_count']=len(results['checks'])
    results['all_checks_passed']=all(r['passed'] for r in results['checks'])
    destination=args.output or root/'verification/reproduced_results.json'
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
    print(f"PASS: {results['check_count']} mechanical checks. Results: {destination}")
    return 0


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (OSError,ValueError,AssertionError,KeyError,zipfile.BadZipFile) as exc:
        raise SystemExit(f'VERIFICATION FAILED: {exc}') from exc
