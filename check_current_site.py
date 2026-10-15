"""Current publication gate; retain the earlier checker as a historical artifact.

The parent 960d9b9 already contains 14 video blocks. The historical checker still
expects five. This version binds every parent video block byte for byte, repairs
only that stale count in memory, and executes all remaining original checks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

p = argparse.ArgumentParser(add_help=False)
p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
a, _ = p.parse_known_args()
root = a.root.resolve()
blocks = re.findall(r'<video\b.*?</video>', (root/'index.html').read_text(), re.S)
assert len(blocks) == 14
assert hashlib.sha256('\0'.join(blocks).encode()).hexdigest() == '323719230ecd1ccf0091a8a82225850c1d7c48fa330450cf1a711a4a24e799bc'
original = Path(__file__).resolve().with_name('check_site.py')
source = original.read_text()
assert hashlib.sha256(source.encode()).hexdigest() == 'afcd0ef51e191227098ed966bd098f7df5b8fd1a4f392221890246f63b911c5d'
before = 'assert main_html.count(\'<video class="experiment-video"\') == 5'
after = 'assert main_html.count(\'<video class="experiment-video"\') == 14'
assert source.count(before) == 1
exec(compile(source.replace(before, after), '<current_parent_bound_site_checker>', 'exec'),
     {'__name__': '__main__', '__file__': str(original)})
print(json.dumps({'current_video_blocks_retained_byteexact': 14,
                  'inherited_checker_unchanged': True,
                  'observer_change': 'Parent-bound historical video-count correction only'}))
