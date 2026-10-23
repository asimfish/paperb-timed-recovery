"""Reproduce the public illustrative chart from the adjacent CSV and summary.
No asset, runtime, private teacher input, credentials or internal path is needed.
Use Python with Matplotlib installed; system Python here uses python3 -s -B.
"""
import argparse
import csv
import json
from pathlib import Path


def render(out):
    root = Path(__file__).resolve().parent
    summary = json.loads((root / 'REPLAY_SUMMARY.json').read_text())
    with (root / 'public_hold_trace.csv').open(newline='') as f:
        data = list(csv.DictReader(f))
    display = [row for row in data if float(row['process_time_s']) <= 230.]
    x = [float(row['process_time_s']) for row in display]
    temperature = [float(row['indicated_delta_K']) for row in display]
    opened = [row['door_observed_open'] == '1' for row in display]
    timer = [float(row['runtime_counter_s']) for row in display]
    proxy = [float(row['public_proxy_s']) for row in display]
    hold = summary['goal']['hold_s'];band = summary['goal']['tolerance_K']
    scale = summary['figure']['process_time_scale']
    effects = summary['figure']['public_effects']
    endpoints = summary['figure']['proxy_endpoints_process_s']
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.labelcolor': '#22313f', 'text.color': '#22313f',
                         'svg.fonttype': 'none', 'pdf.fonttype': 42})
    fig, axes = plt.subplots(2, 1, figsize=(7.5, 4.9), sharex=True,
                             gridspec_kw={'height_ratios': [1, 1.6]})
    fig.subplots_adjust(left=.105, right=.975, bottom=.18, top=.80, hspace=.40)
    fig.text(.105, .94, 'An interrupted hold needs a fresh continuous interval',
             fontsize=14, weight='bold')
    fig.text(.105, .888, 'Recorded public observations  |  Furnace  |  Process clock = simulation clock × %g' % scale,
             fontsize=9, color='#52616e')
    ax = axes[0]
    ax.axhspan(-band, band, color='#dfe9ed', alpha=.75, label='Declared task band')
    ax.plot(x, temperature, color='#0072B2', lw=1.7, label='Indicated temperature')
    ax.set_ylabel('Indicated $T-T^*$ (K)')
    ax.set_title('(a) Door opening interrupts the public hold condition', loc='left', fontsize=10, pad=8)
    ax.set_ylim(min(temperature) - .4, max(1., max(temperature) + .4))
    for capability, t in effects:
        if t <= 230:
            label = 'Open' if capability == 'door.open' else 'Close'
            ax.axvline(t, color='#AD6E00', lw=.9, ls=':')
            ax.text(t+2, .89, label, transform=ax.get_xaxis_transform(), fontsize=8,
                    color='#8c5700', va='top')
    ax.legend(loc='lower left', fontsize=8, frameon=False, ncol=2)
    ax = axes[1]
    ax.plot(x, timer, color='#6b7580', lw=1.7, label='Runtime accumulated counter')
    ax.plot(x, proxy, color='#0072B2', lw=2.1, label='Public continuity proxy')
    ax.axhline(hold, color='#293b46', lw=.9, ls='--', label='Required continuous hold (%g s)' % hold)
    ax.set_title('(b) The counter retains prior hold; the proxy restarts', loc='left', fontsize=10, pad=9)
    ax.set_ylabel('Reported / proxy duration (s)')
    ax.set_xlabel('Process time (s)')
    ax.set_ylim(-7, max(timer + [hold]) + 24)
    for t in endpoints:
        ax.plot(t, hold, marker='o', ms=5, color='#0072B2', zorder=5)
        ax.annotate('Proxy endpoint', (t, hold), xytext=(-7, 14),
                    textcoords='offset points', ha='right', fontsize=8, color='#0072B2')
    for axis in axes:
        lo, hi = axis.get_ylim()
        axis.fill_between(x, lo, hi, where=opened, step='post', color='#E69F00',
                          alpha=.13, linewidth=0, zorder=0)
        axis.grid(axis='y', color='#e5e9ec', lw=.6)
        axis.set_axisbelow(True)
        axis.set_xlim(0, 230)
    ax.legend(loc='upper left', frameon=False, fontsize=8)
    fig.text(.105, .069, 'Shading: door observed open at query times. Lines: delivered public packets only.',
             fontsize=8, color='#52616e')
    fig.text(.105, .029, 'Illustrative replay; proxy ≠ hidden-truth hold, task success, or learned-policy advantage.',
             fontsize=8, color='#52616e')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    for extension in ('png', 'pdf', 'svg'):
        fig.savefig(out / ('public_hold_mechanism.' + extension), dpi=220, facecolor='white')
    plt.close(fig)
    svg = out / 'public_hold_mechanism.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, default=Path('reproduced_public_hold'))
    render(p.parse_args().out)
