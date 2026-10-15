"""Independent SI/contact arithmetic; never imports collector or native SDK."""
from __future__ import annotations

import math


class Rejected(ValueError):
    pass


def number(value, label="number"):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise Rejected(f"{label}: finite real required")
    return float(value)


def integer(value, label="integer", minimum=0):
    if type(value) is not int or value < minimum:
        raise Rejected(f"{label}: integer >= {minimum} required")
    return value


def vector(value, label="vector"):
    if type(value) is not list or len(value) != 3:
        raise Rejected(f"{label}: exact 3-vector required")
    return [number(x, label) for x in value]


def norm(v):
    return math.sqrt(math.fsum(x*x for x in vector(v)))


def add(a, b):
    return [x+y for x, y in zip(vector(a), vector(b))]


def sub(a, b):
    return [x-y for x, y in zip(vector(a), vector(b))]


def scale(a, s):
    s = number(s)
    return [x*s for x in vector(a)]


def near(a, b, atol, rtol=0.0, label="comparison"):
    a, b = vector(a, label), vector(b, label)
    error = norm(sub(a, b))
    tolerance = number(atol) + number(rtol)*max(norm(a), norm(b))
    if error > tolerance:
        raise Rejected(f"{label}: vector error {error:.17g} > {tolerance:.17g}")
    return error


def acceleration(velocity, previous_velocity, dt):
    dt = number(dt, "physics dt")
    if dt <= 0:
        raise Rejected("physics dt must be positive")
    return scale(sub(velocity, previous_velocity), 1.0/dt)


def support_prediction(mass, accel, gravity):
    mass = number(mass, "actual mass")
    if mass <= 0:
        raise Rejected("actual mass must be positive")
    return scale(sub(accel, gravity), mass)


def signed_pair_sum(selected, label="normal detail"):
    """Selected finite signed scalar times original unit normal, no abs/rotation."""
    if type(selected) is not list:
        raise Rejected(f"{label}: selected list required")
    total = [0.0, 0.0, 0.0]
    for item in selected:
        if type(item) is not dict:
            raise Rejected(f"{label}: contact object required")
        scalar = number(item["scalar"], f"{label} scalar")
        normal = vector(item["normal"], f"{label} normal")
        unit_error = abs(norm(normal)-1.0)
        if unit_error > 0.0001:
            raise Rejected(f"{label}: normal unit error {unit_error}")
        total = add(total, scale(normal, scalar))
    return total


def detail_matrix_agreement(selected, matrix, label="detail/matrix"):
    matrix = vector(matrix, label)
    return near(signed_pair_sum(selected, label), matrix,
                max(1e-5, 1e-5*norm(matrix)), label=label)


def dt_consistency(values, dt, label="getter dt"):
    """values are copied getter values at 1, dt, and 2dt; no redivision."""
    if type(values) is not list or len(values) != 3:
        raise Rejected(f"{label}: three getter queries required")
    impulse, force, force_twice_dt = [vector(x, label) for x in values]
    dt = number(dt)
    if dt <= 0:
        raise Rejected("dt must be positive")
    e1 = near(scale(force, dt), impulse, 1e-7, 3e-5,
              f"{label}: F(dt)*dt versus I(1)")
    e2 = near(force_twice_dt, scale(force, 0.5), 1e-5, 3e-5,
              f"{label}: F(2dt) versus half F(dt)")
    return {"impulse_error_Ns": e1, "force_halving_error_N": e2}


def low_motion(linear_velocity, angular_velocity, linear_accel, angular_accel):
    for label, value, limit in (
        ("speed", linear_velocity, 0.005),
        ("angular speed", angular_velocity, 0.02),
        ("acceleration", linear_accel, 0.05),
        ("angular acceleration", angular_accel, 0.1),
    ):
        magnitude = norm(value)
        if magnitude > limit:
            raise Rejected(f"quasistatic {label}: {magnitude} > {limit}")


def freefall(accel, gravity, net):
    return {
        "acceleration_error_m_s2": near(accel, gravity, 0.05, label="freefall acceleration"),
        "net_normal_error_N": near(net, [0, 0, 0], 0.001, label="freefall net normal"),
    }


def static_top(mass, accel, gravity, net_normal, normal_ab, friction_ab):
    gravity = vector(gravity)
    tolerance = max(0.01, 0.02*number(mass)*norm(gravity))
    prediction = support_prediction(mass, accel, gravity)
    # Normal matrix and signed detail describe the same force. Neither is added.
    combined = add(normal_ab, friction_ab)
    errors = {
        "newton_error_N": near(combined, prediction, tolerance, label="A Newton support"),
        "static_mg_error_N": near(combined, scale(gravity, -number(mass)), tolerance, label="A static mg"),
        "net_pair_error_N": near(net_normal, normal_ab, tolerance, label="A net normal versus pair"),
    }
    if norm(friction_ab) > 0.0001:
        raise Rejected("expected zero friction exceeds 0.0001 N")
    return errors


def reciprocal(normal_ab, normal_ba, friction_ab, friction_ba):
    zero = [0, 0, 0]
    return {
        "normal_error_N": near(add(normal_ab, normal_ba), zero, 0.01, label="reciprocal normal"),
        "friction_error_N": near(add(friction_ab, friction_ba), zero, 0.01, label="reciprocal friction"),
        "combined_error_N": near(add(add(normal_ab, friction_ab), add(normal_ba, friction_ba)),
                                  zero, 0.01, label="reciprocal combined"),
    }
