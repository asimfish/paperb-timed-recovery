"""Independent exact integer enumeration of synthetic interval schedules.

The common-denominator transform removes floating-point boundary ambiguity.
No candidate scheduler or producer-side oracle is imported.
"""
from fractions import Fraction
import math


def oracle(case):
    names = ['dt_ratio', 'contact_request_s', 'duration_request_s', 'tolerance_s',
             'min_skill_gap_s', 'earliest_contact_dispatch_s']
    parsed = {name: Fraction(case[name]) for name in names}
    av = [Fraction(x) for x in case['mechanical_contact_interval_s']]
    bv = [Fraction(x) for x in case['mechanical_release_interval_s']]
    if not (parsed['dt_ratio'] > 0 and parsed['tolerance_s'] >= 0 and av[0] <= av[1] and bv[0] <= bv[1]):
        raise ValueError('invalid interval scheduling input')
    scale = math.lcm(*(x.denominator for x in [*parsed.values(), *av, *bv]))
    ints = {name: int(value*scale) for name, value in parsed.items()}
    a0, a1 = [int(value*scale) for value in av]
    b0, b1 = [int(value*scale) for value in bv]
    dt, D, H, e, minimum, earliest = [ints[name] for name in names]
    q = case['public_delay_ticks']*dt
    ceildiv = lambda a, b: -((-a)//b)
    # Broad endpoint windows are independent of the duration constraint.
    lo_a = max(0, ceildiv(D-e-q-a1, dt)-1)
    hi_a = (D+e-q-a0)//dt+1
    lo_b = max(0, ceildiv(D+H-e-q-b1, dt)-1)
    hi_b = (D+H+e-q-b0)//dt+1
    valid_a = [i for i in range(lo_a, hi_a+1) if D-e <= i*dt+q+a0 and i*dt+q+a1 <= D+e]
    valid_b = [i for i in range(lo_b, hi_b+1) if D+H-e <= i*dt+q+b0 and i*dt+q+b1 <= D+H+e]
    ideal_a_twice = 2*(D-q)-(a0+a1)
    ideal_b_twice = 2*(D+H-q)-(b0+b1)
    feasible = []
    best = None
    for ai in valid_a:
        for bi in valid_b:
            delta = (bi-ai)*dt
            if ai*dt < earliest or delta < minimum:
                continue
            corners = [delta+bl-al for al in (a0, a1) for bl in (b0, b1)]
            if not all(H-e <= value <= H+e for value in corners):
                continue
            feasible.append([ai, bi])
            squared = (2*ai*dt-ideal_a_twice)**2+(2*bi*dt-ideal_b_twice)**2
            choice = (squared, ai, bi)
            if best is None or choice < best:
                best = choice
    return {'feasible_pairs': feasible, 'feasible_pair_count': len(feasible),
            'selected_ticks': [best[1], best[2]] if best else None,
            'objective_ratio': str(Fraction(best[0], 4*scale*scale)) if best else None,
            'absolute_a_ticks': valid_a, 'absolute_b_ticks': valid_b,
            'integer_common_denominator': scale, 'pairs_checked': len(valid_a)*len(valid_b)}


def classify(case, selected):
    if selected is None:
        return {'contact': False, 'release': False, 'duration_gap': False, 'min_skill': False, 'joint': False}
    dt = Fraction(case['dt_ratio'])
    a, b = [i*dt for i in selected]
    delay = case['public_delay_ticks']*dt
    D, H, e = [Fraction(case[k]) for k in ('contact_request_s', 'duration_request_s', 'tolerance_s')]
    ma, mb = [list(map(Fraction, case[k])) for k in ('mechanical_contact_interval_s', 'mechanical_release_interval_s')]
    ca = all(D-e <= a+delay+x <= D+e for x in ma)
    cb = all(D+H-e <= b+delay+x <= D+H+e for x in mb)
    cd = all(H-e <= b-a+y-x <= H+e for x in ma for y in mb)
    cs = a >= Fraction(case['earliest_contact_dispatch_s']) and b-a >= Fraction(case['min_skill_gap_s'])
    return dict(contact=ca, release=cb, duration_gap=cd, min_skill=cs, joint=ca and cb and cd and cs)
