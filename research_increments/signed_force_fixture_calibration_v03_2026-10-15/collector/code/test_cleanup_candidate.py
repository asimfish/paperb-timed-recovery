import ast
import json
from pathlib import Path
import unittest
from close_regression_model import run_counterfactual


class CleanupCandidateTests(unittest.TestCase):
    def test_exact_installed_STOP_callback_is_red_without_public_clear(self):
        row=run_counterfactual(clear=False)
        self.assertEqual(row['status'],'RED_STOP_CALLBACK_WOULD_REENTER_RENDER')
        self.assertEqual(row['render_trap_calls'],1);self.assertTrue(row['own_stop_subscription_active'])
    def test_exact_installed_public_clear_removes_owned_callback_green(self):
        row=run_counterfactual(clear=True)
        self.assertEqual(row['status'],'GREEN_OWNED_STOP_SUBSCRIPTION_RELEASED')
        self.assertEqual(row['render_trap_calls'],0);self.assertEqual(row['own_stop_unsubscribe_calls'],1)
        self.assertTrue(row['old_own_stop_handle_is_None']);self.assertTrue(row['public_singleton_is_None'])
        self.assertEqual(row['remaining_owned_callback_dict_entries'],0);self.assertTrue(row['unrelated_subscription_active'])
    def test_inherited_positive_physics_and_cleanup_unchanged(self):
        root=Path(__file__).parent.parent;new=json.loads((root/'protocol.json').read_text());old=json.loads((root/'PARENT_FROZEN_FORCE_PROTOCOL_V02.json').read_text())
        self.assertEqual(len(new['cases']),6);self.assertEqual(new['cleanup_candidate'],old['cleanup_candidate'])
        self.assertEqual(new['dt_s'],old['dt_s']);self.assertEqual(new['setup'],old['setup'])
        for candidate,parent in zip(new['cases'][1:],old['cases']):
            normalized=candidate.copy();normalized.pop('measurement_role');normalized.pop('contact_processing_disabled_requested');normalized['id']=parent['id']
            self.assertEqual(normalized,parent)
        self.assertEqual(new['max_worker_seconds'],300);self.assertEqual(new['termination_wait_s'],30)
    def test_clear_only_terminal_and_default_close_stays_zero_args(self):
        tree=ast.parse((Path(__file__).parent/'native_probe.py').read_text());calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
        close=[n for n in calls if isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='app' and n.func.attr=='close']
        clear=[n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='clear_instance']
        self.assertEqual(len(close),1);self.assertFalse(close[0].args);self.assertFalse(close[0].keywords);self.assertEqual(len(clear),1)
        fsyncmark=next(n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='mark' and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value=='AFTER_RESULT_FSYNC')
        self.assertGreater(clear[0].lineno,fsyncmark.lineno);self.assertLess(clear[0].lineno,close[0].lineno)
        eligible=[n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.BoolOp) and 'end_fsynced' in ast.unparse(n.test) and 'result_fsynced' in ast.unparse(n.test)]
        self.assertEqual(len(eligible),1);self.assertIn(clear[0],list(ast.walk(eligible[0])))
        for marker in ('AFTER_CLEAR_INSTANCE','AFTER_APP_CLOSE'):
            node=next(n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='mark' and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value==marker)
            self.assertIsNone(next(k.value.value for k in node.keywords if k.arg=='clock_read'))


if __name__=='__main__':unittest.main(verbosity=2)
