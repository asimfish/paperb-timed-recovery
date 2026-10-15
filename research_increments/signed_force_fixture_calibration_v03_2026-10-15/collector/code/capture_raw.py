"""SDK-free exact selected-slot copies; no force interpretation or qualification."""
import hashlib
import json
import math


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha_value(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def plain(value):
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError('NONFINITE_ACTUAL_VALUE')
        return value
    if type(value) in (list, tuple):
        return [plain(v) for v in value]
    if hasattr(value, 'detach'):
        return plain(value.detach().cpu().tolist())
    if hasattr(value, 'tolist'):
        return plain(value.tolist())
    if all(hasattr(value, x) for x in ('x', 'y', 'z')):
        return [float(value.x), float(value.y), float(value.z)]
    raise TypeError('UNSUPPORTED_SDK_VALUE')


def shape(value):
    return [int(x) for x in value.shape]


def selected_copy(raw, *, kind, sensors, filters, capacity):
    names = ['forces', 'points', 'normals', 'separations', 'counts', 'starts'] if kind == 'normal' else ['forces', 'points', 'counts', 'starts']
    if len(raw) != len(names):
        raise ValueError('UNEXPECTED_DETAIL_ARITY')
    counts = plain(raw[-2]); starts = plain(raw[-1])
    if len(counts) != sensors or len(starts) != sensors:
        raise ValueError('COUNT_START_SENSOR_SHAPE')
    selected = set()
    for s in range(sensors):
        if len(counts[s]) != filters or len(starts[s]) != filters:
            raise ValueError('COUNT_START_FILTER_SHAPE')
        for f in range(filters):
            count, start = counts[s][f], starts[s][f]
            if type(count) is not int or type(start) is not int or count < 0 or start < 0 or start + count > capacity:
                raise ValueError('SELECTED_RANGE_INVALID')
            indices = set(range(start, start + count))
            if selected & indices:
                raise ValueError('OVERLAPPING_SELECTED_RANGES')
            selected.update(indices)
    result = {'counts': counts, 'starts': starts, 'capacity': capacity,
              'buffer_shapes': {name: shape(array) for name, array in zip(names, raw)},
              'selected_slot_indices': sorted(selected),
              'unused_slot_policy': 'NULL_MARKER_NOT_READ_NOT_ZERO_IMPUTED',
              'capacity_saturated': len(selected) >= capacity}
    for name, array in zip(names[:-2], raw[:-2]):
        if shape(array)[0] != capacity:
            raise ValueError('BUFFER_CAPACITY_SHAPE')
        copied = [None] * capacity
        for index in sorted(selected):
            copied[index] = plain(array[index])
        result[name] = copied
    result['copied_payload_sha256'] = sha_value(result)
    return result


def observed(clock_read, getter, copier=plain):
    before = clock_read()
    try:
        value = copier(getter())
        status, reason = 'OBSERVED', None
    except Exception as exc:
        value, status = None, 'UNKNOWN'
        reason = {'exception_type': type(exc).__name__, 'message': str(exc)}
    after = clock_read()
    return {'status': status, 'value': value, 'reason': reason,
            'clock_before': before, 'clock_after': after,
            'no_step_during_getter': before == after}


def query_contact(view, query_dt, clock_read, configured_details):
    before = clock_read()
    out = {'query_dt_s': query_dt,
           'net_normal': observed(clock_read, lambda: view.get_net_contact_forces(query_dt))}
    if configured_details:
        out['matrix_normal'] = observed(clock_read, lambda: view.get_contact_force_matrix(query_dt))
        out['normal_detail'] = observed(clock_read, lambda: view.get_contact_data(query_dt),
            lambda data: selected_copy(data, kind='normal', sensors=int(view.sensor_count),
                                      filters=int(view.filter_count), capacity=int(view.max_contact_data_count)))
        out['friction_detail'] = observed(clock_read, lambda: view.get_friction_data(query_dt),
            lambda data: selected_copy(data, kind='friction', sensors=int(view.sensor_count),
                                      filters=int(view.filter_count), capacity=int(view.max_contact_data_count)))
    else:
        out['unconfigured_channels'] = ['matrix_normal', 'normal_detail', 'friction_detail']
        out['channel_scope'] = 'INTENTIONALLY_NOT_CONFIGURED_FREEFALL'
    after = clock_read()
    out['clock_before'], out['clock_after'] = before, after
    out['no_step_during_query'] = before == after
    return out
