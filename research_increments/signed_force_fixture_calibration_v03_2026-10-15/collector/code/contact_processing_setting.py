"""Worker-local contact-report processing, explicit setter and actual readback.

No SDK import, force scaling, frame conversion or qualification. The caller
injects its current Kit settings interface. Missing/non-boolean values UNKNOWN.
"""
PATH = '/physics/disableContactProcessing'


def read_processing_setting(settings, *, clock_read=None):
    before = clock_read() if clock_read is not None else None
    try:
        value = settings.get(PATH)
        if type(value) is not bool:
            result = {'status':'UNKNOWN','value':None,'reason':'ACTUAL_SETTING_NOT_BUILTIN_BOOL',
                'actual_returned_type':type(value).__name__}
        else:
            result = {'status':'OBSERVED','value':value,'reason':None}
    except Exception as exc:
        result = {'status':'UNKNOWN','value':None,'reason':'GETTER_EXCEPTION',
            'exception_type':type(exc).__name__,'exception_message':str(exc)}
    after = clock_read() if clock_read is not None else None
    result.update(schema='WorkerLocalContactProcessingReadback/1',setting_path=PATH,
        getter='carb.settings.get_settings().get(path)',worker_local_scope=True,
        native_clock_before=before,native_clock_after=after,
        no_native_step_during_readback=before==after if before is not None and after is not None else None,
        readback_not_force_physics_qualification=True)
    return result


def install_processing_setting(settings, requested_disabled):
    if type(requested_disabled) is not bool:
        raise ValueError('EXPLICIT_CASE_BOUND_DISABLED_BOOLEAN_REQUIRED')
    before = read_processing_setting(settings)
    settings.set_bool(PATH,requested_disabled)
    after = read_processing_setting(settings)
    return {'schema':'WorkerLocalContactProcessingInstallation/1',
        'phase':'AFTER_CONTEXT_CONSTRUCTION_BEFORE_RESET','requested_disabled':requested_disabled,
        'actual_before':before,'actual_after':after,
        'actual_matches_requested':after['status']=='OBSERVED' and after['value'] is requested_disabled,
        'setter':'carb.settings.get_settings().set_bool(path,requested_disabled)',
        'scope':'CURRENT_OWNED_WORKER_PROCESS_NOT_GLOBAL_GPU_DRIVER'}
