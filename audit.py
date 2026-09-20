"""Compare synthetic report snapshots using SQL keys and Decimal tolerances."""
from __future__ import annotations

import csv
import json
import random
import sqlite3
from collections import Counter
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEYS = ('metric', 'period', 'plan', 'cohort')
DEFINITIONS = ('unit', 'time_basis', 'denominator', 'filters')
FIELDS = KEYS + ('value',) + DEFINITIONS
SEED = 20260921


def policies():
    return json.loads((ROOT/'policies.json').read_text())


def decimal_text(value, places=4):
    return str(Decimal(value).quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP))


def generate_snapshots():
    rng = random.Random(SEED)
    policy = policies()
    source = []
    for period in ('2024', '2025'):
        for plan in ('PPO', 'HDHP'):
            members = rng.randint(300, 750)
            continuous = rng.randint(180, members-30)
            partial = members-continuous
            continuous_cost = Decimal(rng.randint(65000,105000))*continuous*12/100
            partial_cost = Decimal(rng.randint(65000,105000))*partial*6/100
            continuous_episodes = rng.randint(35,continuous//2)
            partial_episodes = rng.randint(1,partial//2)
            continuous_admissions,partial_admissions = rng.randint(10,50),rng.randint(2,20)
            continuous_risk,partial_risk = Decimal(rng.randint(700,1600))/1000,Decimal(rng.randint(700,1600))/1000
            for cohort, n, months in (
                ('All enrolled', members, continuous*12 + (members-continuous)*6),
                ('Continuous enrollment', continuous, continuous*12),
            ):
                is_continuous = cohort=='Continuous enrollment'
                allowed = continuous_cost if is_continuous else continuous_cost+partial_cost
                episodes = continuous_episodes if is_continuous else continuous_episodes+partial_episodes
                admissions = continuous_admissions if is_continuous else continuous_admissions+partial_admissions
                risk = continuous_risk if is_continuous else (continuous_risk*continuous+partial_risk*partial)/members
                values = {
                    'allowed_cost': allowed,
                    'member_months': Decimal(months),
                    'pmpm': allowed/months,
                    'members_with_episode_pct': Decimal(episodes)*100/n,
                    'admissions_per_1000': Decimal(admissions)*1000/n,
                    'risk_score': risk,
                }
                denominator = {'pmpm':'enrolled_member_months','members_with_episode_pct':'enrolled_members',
                               'admissions_per_1000':'enrolled_members/1000','risk_score':'scored_members'}
                for metric,value in values.items():
                    source.append(dict(metric=metric, period=period, plan=plan, cohort=cohort,
                        value=decimal_text(value,0 if metric=='member_months' else 4), unit=policy[metric]['unit'],
                        time_basis='incurred_calendar_year', denominator=denominator.get(metric,'not_applicable'),
                        filters='providers=all;status=eligible'))
    target = [dict(row) for row in source]
    def pick(rows, metric, period='2025', plan='PPO', cohort='All enrolled'):
        return next(row for row in rows if tuple(row[k] for k in KEYS)==(metric,period,plan,cohort))
    # One known case per issue. Equal numbers can still have different definitions.
    missing=pick(target,'member_months');target.remove(missing)
    duplicate=pick(target,'risk_score');target.append(dict(duplicate))
    pick(target,'pmpm')['value']=str(Decimal(pick(source,'pmpm')['value'])+Decimal('4.20'))
    pick(target,'members_with_episode_pct')['denominator']='members_with_claims'
    unit=pick(target,'members_with_episode_pct',plan='HDHP')
    unit['unit']='proportion';unit['value']=str(Decimal(unit['value'])/100)
    pick(target,'admissions_per_1000')['filters']='providers=top10;status=eligible'
    pick(target,'allowed_cost')['value']='not_available'
    target.append(dict(pick(source,'member_months'),period='2026',value='4800'))
    # Rounding differences are within the declared absolute tolerance.
    for metric,delta in [('allowed_cost','0.01'),('pmpm','0.005'),('risk_score','0.001'),('admissions_per_1000','0.05')]:
        row=pick(target,metric,period='2024',plan='HDHP',cohort='Continuous enrollment')
        row['value']=str(Decimal(row['value'])+Decimal(delta))
    return source,target


def load_table(connection, name, rows):
    # Names are supplied only by this module; snapshot values use SQL parameters.
    if name not in ('source_snapshot','target_snapshot'):
        raise ValueError('Unknown snapshot table')
    connection.execute(f'CREATE TABLE {name} ('+', '.join(f'{field} TEXT' for field in FIELDS)+')')
    for row in rows:
        if any(not str(row.get(field,'')).strip() for field in KEYS):
            raise ValueError('Snapshot row has an empty business key')
    connection.executemany(f'INSERT INTO {name} VALUES ('+','.join('?' for _ in FIELDS)+')',
                           [[row.get(field) for field in FIELDS] for row in rows])


def classify(row, policy):
    result=dict(row, delta=None, absolute_tolerance=None, relative_change_pct=None, definition_changes=[])
    reasons=[]
    if row['source_count']==0:reasons.append('unexpected_target')
    if row['target_count']==0:reasons.append('missing_target')
    if row['source_count']>1:reasons.append('duplicate_source')
    if row['target_count']>1:reasons.append('duplicate_target')
    if not reasons:
        rule=policy.get(row['metric'])
        if rule is None:
            reasons.append('missing_policy')
        else:
            result['absolute_tolerance']=rule['absolute_tolerance']
            for field in DEFINITIONS:
                a,b=row['source_'+field],row['target_'+field]
                if not a or not b:
                    reasons.append('incomplete_definition')
                elif a != b:
                    result['definition_changes'].append({'field':field,'source':a,'target':b})
            if result['definition_changes']:reasons.append('definition_mismatch')
            if row['source_unit']!=rule['unit'] or row['target_unit']!=rule['unit']:
                reasons.append('unit_policy_mismatch')
            try:
                before,after=Decimal(row['source_value']),Decimal(row['target_value'])
                if not before.is_finite() or not after.is_finite():raise InvalidOperation
                if before<0 or after<0:raise InvalidOperation
                if rule['integer'] and (before!=before.to_integral_value() or after!=after.to_integral_value()):raise InvalidOperation
            except (InvalidOperation,ValueError,TypeError):
                reasons.append('invalid_value')
            if not reasons:
                delta=after-before
                result['delta']=str(delta)
                result['relative_change_pct']=str((delta/before*100).quantize(Decimal('.0001'))) if before else None
                if abs(delta)>Decimal(rule['absolute_tolerance']):reasons.append('value_mismatch')
                else:
                    result['status']='within_tolerance' if delta else 'exact_match'
                    result['needs_review']=False
                    result['reasons']=[]
                    return result
    result['status']=reasons[0]
    result['needs_review']=True
    result['reasons']=list(dict.fromkeys(reasons))
    return result


def reconcile(source, target, policy=None):
    connection=sqlite3.connect(':memory:')
    connection.row_factory=sqlite3.Row
    load_table(connection,'source_snapshot',source)
    load_table(connection,'target_snapshot',target)
    rows=[classify(dict(row),policy if policy is not None else policies())
          for row in connection.execute((ROOT/'sql/reconcile.sql').read_text())]
    connection.close()
    return rows


def write_csv(path,rows,fields=None):
    with path.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=fields or list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def run():
    data,output=ROOT/'data',ROOT/'outputs'
    data.mkdir(exist_ok=True);output.mkdir(exist_ok=True)
    source,target=generate_snapshots()
    write_csv(data/'source_snapshot.csv',source,FIELDS)
    write_csv(data/'target_snapshot.csv',target,FIELDS)
    rows=reconcile(source,target)
    expected=set(tuple(row[k] for k in KEYS) for row in source+target)
    counts=Counter(row['status'] for row in rows)
    checks={
        'one_result_per_union_key':len(rows)==len(expected)==len({tuple(row[k] for k in KEYS) for row in rows}),
        'source_row_counts_reconcile':sum(row['source_count'] for row in rows)==len(source),
        'target_row_counts_reconcile':sum(row['target_count'] for row in rows)==len(target),
        'review_and_pass_totals_reconcile':sum(row['needs_review'] for row in rows)+sum(not row['needs_review'] for row in rows)==len(expected),
    }
    if not all(checks.values()):raise RuntimeError(f'Reconciliation failed: {checks}')
    summary={'source_rows':len(source),'target_rows':len(target),'compared_keys':len(rows),
             'review':sum(row['needs_review'] for row in rows),'passed':sum(not row['needs_review'] for row in rows),
             'status_counts':dict(sorted(counts.items())),'checks':checks}
    payload={'data_kind':'synthetic','ai_assisted':True,'seed':SEED,'summary':summary,'policies':policies(),'results':rows}
    (output/'audit.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    if (ROOT/'dashboard').is_dir():
        (ROOT/'dashboard/data.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    export=[dict(data_kind='synthetic',**{key:value for key,value in row.items() if key not in ('definition_changes','reasons')},
                 reasons='; '.join(row['reasons']),definition_changes=json.dumps(row['definition_changes'])) for row in rows]
    write_csv(output/'audit.csv',export)
    findings=f'''# Findings: fictional reporting migration\n\nAn AI-assisted portfolio example. Both snapshots are generated; no employer report definitions or client results are included.\n\n## Audit summary\n\n- {len(source)} source rows and {len(target)} target rows.\n- **{len(rows)} distinct business keys** across the union of snapshots.\n- **{summary['review']} keys need review**; **{summary['passed']} pass** the declared comparisons.\n- Passing keys include {counts['within_tolerance']} nonzero differences inside the explicit tolerance.\n\n## Review ledger\n\n| Metric | Period | Plan | Cohort | Issue |\n|---|---|---|---|---|\n'''
    for row in rows:
        if row['needs_review']:
            findings+='| '+' | '.join(str(row[k]) for k in KEYS)+' | '+', '.join(row['reasons'])+' |\n'
    findings+='''\n## Suggested review order\n\n1. Resolve missing and duplicate keys before interpreting totals. Duplicate values are withheld from comparison to avoid an arbitrary row choice or join fan-out.\n2. Align units, denominator definitions, time basis, and filter metadata before comparing numbers. Equal values do not prove that definitions agree.\n3. Investigate values outside the declared absolute tolerance; never expand the tolerance just to make a discrepancy pass.\n4. Re-run the audit and retain the issue ledger for review.\n\n## Interpretation limit\n\nThese issues were deliberately injected. Finding them demonstrates the checks on this fixture, not a measured detection rate on real migrations. Definition comparison uses exact documented strings; it cannot inspect an undocumented calculation, validate clinical logic, or detect shared errors in both snapshots. This audit supports review and does not certify a migration.\n'''
    (output/'findings.md').write_text(findings)
    print(json.dumps(summary,indent=2))
    return payload


if __name__=='__main__':
    run()
