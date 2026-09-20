import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit import reconcile


def row(value='100.00',**changes):
    base=dict(metric='pmpm',period='2025',plan='PPO',cohort='All enrolled',value=value,
              unit='USD/member/month',time_basis='incurred_calendar_year',
              denominator='enrolled_member_months',filters='providers=all;status=eligible')
    base.update(changes);return base


class AuditTests(unittest.TestCase):
    def test_decimal_tolerance_is_inclusive(self):
        self.assertEqual(reconcile([row()],[row('100.01')])[0]['status'],'within_tolerance')
        self.assertEqual(reconcile([row()],[row('100.0101')])[0]['status'],'value_mismatch')
        self.assertEqual(reconcile([row()],[row('99.99')])[0]['status'],'within_tolerance')

    def test_equal_values_do_not_hide_changed_denominators(self):
        result=reconcile([row()],[row(denominator='claimant_months')])[0]
        self.assertIn('definition_mismatch',result['reasons'])
        self.assertIsNone(result['delta'])

    def test_duplicates_do_not_create_join_fanout(self):
        result=reconcile([row(),row('101')],[row(),row('102')])
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['source_count'],2)
        self.assertCountEqual(result[0]['reasons'],['duplicate_source','duplicate_target'])
        self.assertIsNone(result[0]['source_value'])

    def test_missing_and_unexpected_keys_are_both_retained(self):
        result=reconcile([row()],[row(plan='HDHP')])
        self.assertCountEqual([r['status'] for r in result],['missing_target','unexpected_target'])

    def test_zero_baseline_uses_absolute_tolerance(self):
        result=reconcile([row('0')],[row('0.02')])[0]
        self.assertEqual(result['status'],'value_mismatch')
        self.assertIsNone(result['relative_change_pct'])

    def test_nonfinite_blank_and_fractional_counts_are_invalid(self):
        for value in ('NaN','Infinity','',None):
            with self.subTest(value=value):
                self.assertIn('invalid_value',reconcile([row()],[row(value)])[0]['reasons'])
        source=row('12',metric='member_months',unit='member-months')
        self.assertIn('invalid_value',reconcile([source],[dict(source,value='12.5')])[0]['reasons'])

    def test_units_and_required_policies_are_checked(self):
        self.assertIn('unit_policy_mismatch',reconcile([row()],[row(unit='USD')])[0]['reasons'])
        self.assertEqual(reconcile([row()],[row()],policy={})[0]['status'],'missing_policy')

    def test_period_plan_and_cohort_are_part_of_the_key(self):
        source=[row(period='2024'),row(),row(plan='HDHP'),row(cohort='Continuous enrollment')]
        result=reconcile(source,[dict(r) for r in source])
        self.assertEqual(len(result),4)
        self.assertTrue(all(r['status']=='exact_match' for r in result))


if __name__=='__main__':
    unittest.main()
