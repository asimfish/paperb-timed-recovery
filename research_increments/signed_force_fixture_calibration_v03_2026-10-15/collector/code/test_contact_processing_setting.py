"""Worker-local setting observations, exact SDK toggle AST, no SDK import."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from contact_processing_setting import PATH,install_processing_setting,read_processing_setting


class FakeSettings:
    def __init__(self,value):self.value=value;self.writes=[]
    def get(self,path):
        if path!=PATH:raise KeyError(path)
        return self.value
    def set_bool(self,path,value):
        self.writes.append([path,value]);self.value=value


class ProcessingTests(unittest.TestCase):
    def test_requested_false_changes_actual_true_and_reads_it(self):
        settings=FakeSettings(True);row=install_processing_setting(settings,False)
        self.assertEqual(settings.writes,[[PATH,False]])
        self.assertIs(row['actual_before']['value'],True);self.assertIs(row['actual_after']['value'],False)
        self.assertTrue(row['actual_matches_requested'])
    def test_negativecontrol_explicit_true(self):
        settings=FakeSettings(False);row=install_processing_setting(settings,True)
        self.assertIs(row['actual_after']['value'],True);self.assertEqual(settings.writes,[[PATH,True]])
    def test_missing_or_nonbool_is_unknown_not_imputed(self):
        for value in (None,0,1,'False'):
            with self.subTest(value=value):
                row=read_processing_setting(FakeSettings(value));self.assertEqual(row['status'],'UNKNOWN');self.assertIsNone(row['value'])
    def test_setter_ignored_is_visible_not_synthetic_match(self):
        settings=FakeSettings(True);settings.set_bool=lambda path,value:None
        row=install_processing_setting(settings,False)
        self.assertIs(row['actual_after']['value'],True);self.assertFalse(row['actual_matches_requested'])
    def test_nonbool_request_refused_beforewrite(self):
        settings=FakeSettings(True)
        for value in (None,0,1,'False'):
            with self.assertRaises(ValueError):install_processing_setting(settings,value)
        self.assertEqual(settings.writes,[])
    def test_readonly_observation_clockchange_explicit(self):
        clocks=iter([{'callback_count':1},{'callback_count':2}]);settings=FakeSettings(False)
        row=read_processing_setting(settings,clock_read=lambda:next(clocks))
        self.assertFalse(row['no_native_step_during_readback']);self.assertEqual(settings.writes,[])
    def test_getter_exception_unknown(self):
        settings=FakeSettings(True);settings.get=lambda path:(_ for _ in ()).throw(RuntimeError('missing interface'))
        self.assertEqual(read_processing_setting(settings)['status'],'UNKNOWN')
    def test_exact_pinned_context_and_sensor_AST_toggle_samekey(self):
        root=Path(__file__).parent.parent;pins=json.loads((root/'INSTALLED_API_PIN.json').read_text())['files']
        cases=[('isaaclab_simulation_context','SimulationContext','_apply_physics_settings',True),('contact_sensor','ContactSensor','__init__',False)]
        events=[]
        for key,clsname,method,expected in cases:
            source=Path(pins[key]['path']);self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),pins[key]['sha256'])
            tree=ast.parse(source.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==clsname)
            function=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==method)
            calls=[n for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='set_bool' and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value==PATH]
            self.assertEqual(len(calls),1);self.assertIs(calls[0].args[1].value,expected)
            statements=[n for n in function.body if isinstance(n,ast.Expr) and n.value is calls[0]]
            self.assertEqual(len(statements),1)
            settings=FakeSettings(not expected)
            namespace={'self':SimpleNamespace(carb_settings=settings),'carb_settings_iface':settings}
            # Execute exact vendor setter statement only; avoid unrelated SDK
            # settings/stage construction and any framework import.
            module=ast.fix_missing_locations(ast.Module(body=statements,type_ignores=[]))
            exec(compile(module,str(source)+'#exact_contact_toggle_CPU_seam','exec'),namespace)
            self.assertIs(settings.value,expected);events.append([clsname,expected])
        self.assertEqual(events,[['SimulationContext',True],['ContactSensor',False]])
    def test_install_before_reset_and_readback_at_everyboundary_AST(self):
        tree=ast.parse((Path(__file__).parent/'native_probe.py').read_text());calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
        install=[n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='install_processing_setting'];self.assertEqual(len(install),1)
        reset=[n for n in calls if isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='sim' and n.func.attr=='reset'];self.assertEqual(len(reset),1);self.assertLess(install[0].lineno,reset[0].lineno)
        readbacks=[n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='read_processing_setting'];self.assertEqual(len(readbacks),4)
        loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='tick')
        self.assertEqual(sum(n in list(ast.walk(loop)) for n in readbacks),1)
    def test_six_case_budget_and_identical_physical_parent_dicts(self):
        root=Path(__file__).parent.parent;new=json.loads((root/'protocol.json').read_text());old=json.loads((root/'PARENT_FROZEN_FORCE_PROTOCOL_V02.json').read_text())
        self.assertEqual(len(new['cases']),6);self.assertEqual(sum(c['controlled_steps'] for c in new['cases']),5365)
        self.assertEqual(new['candidate_acceptance'],old['candidate_acceptance']);self.assertEqual(new['prospective_fixed_windows'],old['prospective_fixed_windows']);self.assertEqual(new['dt_s'],old['dt_s']);self.assertEqual(new['setup'],old['setup'])
        for child,parent in zip(new['cases'][1:],old['cases']):
            normalized=child.copy();self.assertIs(normalized.pop('contact_processing_disabled_requested'),False);normalized.pop('measurement_role');normalized['id']=parent['id'];self.assertEqual(normalized,parent)
        off=new['cases'][0].copy();self.assertIs(off.pop('contact_processing_disabled_requested'),True);off.pop('measurement_role');off.pop('positive_reference_case_id');off.pop('negative_control_expected_scope');off['id']=old['cases'][1]['id'];self.assertEqual(off,old['cases'][1])
        self.assertEqual(new['family_budget']['calibration_family_cumulative_upper_bound'],9)


if __name__=='__main__':unittest.main(verbosity=2)
