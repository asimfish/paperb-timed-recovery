"""Exact installed SDK method ASTs on a bounded fake STOP callback seam.

No Isaac/Omni/Carb SDK import. No native app or GPU. The fake render raises at
the first iteration, preserving a RED-capable counterfactual without a CPU hang.
"""
import ast
import copy
import gc
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent
LAB = Path('/home/liyufeng/safeduo_isaaclab/source/isaaclab/isaaclab/sim/simulation_context.py')
BASE = Path('/home/liyufeng/miniforge3/envs/safeduo/lib/python3.11/site-packages/isaacsim/exts/isaacsim.core.api/isaacsim/core/api/simulation_context/simulation_context.py')


class StopHandlerWouldSpin(RuntimeError):
    pass


def method(path, name):
    tree = ast.parse(path.read_text())
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'SimulationContext']
    if len(classes) != 1:
        raise ValueError('EXACT_INSTALLED_CONTEXT_CLASS_REQUIRED')
    methods = [node for node in classes[0].body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(methods) != 1:
        raise ValueError('EXACT_INSTALLED_METHOD_REQUIRED:' + name)
    return copy.deepcopy(methods[0])


def installed_method_pin_gate(root=None):
    pin_root = Path(root) if root is not None else (ROOT.parent if ROOT.name == 'code' and ROOT.parent.name == 'collector' else ROOT)
    pins = json.loads((pin_root / 'INSTALLED_API_PIN.json').read_text())['files']
    for path in (LAB, BASE):
        selected = [pin for pin in pins.values() if pin['path'] == str(path)]
        if len(selected) != 1 or hashlib.sha256(path.read_bytes()).hexdigest() != selected[0]['sha256']:
            raise ValueError('INSTALLED_METHOD_SOURCE_CHANGED')


def run_counterfactual(*, clear):
    installed_method_pin_gate()
    timeline = SimpleNamespace(is_playing=lambda: False)
    manager_events = []
    manager = SimpleNamespace(set_backend=lambda value: manager_events.append(['backend', value]),
        set_physics_sim_device=lambda value: manager_events.append(['device', value]))
    namespace = {'omni': SimpleNamespace(timeline=SimpleNamespace(get_timeline_interface=lambda: timeline)),
        'carb': SimpleNamespace(events=SimpleNamespace(IEvent=object)),
        'SimulationManager': manager, 'gc': gc}
    base_class = ast.ClassDef(name='SimulationContext', bases=[], keywords=[], decorator_list=[],
        body=[ast.parse('_instance = None').body[0], ast.parse('_sim_context_initialized = True').body[0],
              method(BASE,'clear_instance'), method(BASE,'clear_all_callbacks')])
    lab_class = ast.ClassDef(name='LabSimulationContext', bases=[ast.Name(id='SimulationContext',ctx=ast.Load())],
        keywords=[], decorator_list=[], body=[method(LAB,'clear_instance'), method(LAB,'_app_control_on_stop_handle_fn')])
    module = ast.fix_missing_locations(ast.Module(body=[base_class,lab_class],type_ignores=[]))
    exec(compile(module, str(LAB)+'#exact_installed_AST_CPU_seam', 'exec'), namespace)
    base, lab = namespace['SimulationContext'], namespace['LabSimulationContext']
    owner = lab(); renders = []
    def render():
        renders.append('would_render_while_STOPPED')
        raise StopHandlerWouldSpin('EXACT_SDK_STOP_HANDLER_REENTERED_RENDER_WHILE_TIMELINE_NOT_PLAYING')
    owner.render = render; owner._disable_app_control_on_stop_handle = False
    for name in ('_physics_callback_functions','_physics_functions','_stage_callback_functions',
                 '_timeline_callback_functions','_render_callback_functions'):
        setattr(owner,name,{'owned':'callback'})
    owner._stage_open_callback = 'owned'; owner._physics_timer_callback = 'owned'; owner._event_timer_callback = 'owned'
    class Subscription:
        def __init__(self): self.active=True; self.unsubscribes=0
        def unsubscribe(self): self.active=False; self.unsubscribes+=1
    stop = Subscription(); owner._app_control_on_stop_handle=stop
    base._instance=owner
    # Emulates the already-observed stage-close STOP delivery to this one owned
    # subscription; an unrelated observer remains subscribed and is not cleared.
    unrelated = Subscription()
    if clear:
        lab.clear_instance()
    red = False
    try:
        if stop.active:
            owner._app_control_on_stop_handle_fn(SimpleNamespace(type='STOP'))
    except StopHandlerWouldSpin:
        red = True
    result = {'schema':'ExactInstalledStopCallbackCPUCounterfactual/1',
        'status':'RED_STOP_CALLBACK_WOULD_REENTER_RENDER' if red else 'GREEN_OWNED_STOP_SUBSCRIPTION_RELEASED',
        'candidate_clear_invoked':clear,'render_trap_calls':len(renders),
        'own_stop_subscription_active':stop.active,'own_stop_unsubscribe_calls':stop.unsubscribes,
        'old_own_stop_handle_is_None':owner._app_control_on_stop_handle is None,
        'public_singleton_is_None':base._instance is None,
        'unrelated_subscription_active':unrelated.active,
        'remaining_owned_callback_dict_entries':sum(len(getattr(owner,name)) for name in
            ('_physics_callback_functions','_physics_functions','_stage_callback_functions','_timeline_callback_functions','_render_callback_functions')),
        'actual_installed_parent_clear_manager_calls':manager_events,
        'native_GPU_SDK_imports':0,'real_native_shutdown_proven':False,
        'scope':'EXACT_INSTALLED_PYTHON_METHOD_AST_ON_FAKE_STOP_DELIVERY_NOT_REAL_CARB_USD_OR_FRAMEWORK'}
    return result


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(allow_abbrev=False)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--without-clear',action='store_true');group.add_argument('--with-clear',action='store_true')
    args=parser.parse_args();result=run_counterfactual(clear=args.with_clear)
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(2 if result['status'].startswith('RED_') else 0)
