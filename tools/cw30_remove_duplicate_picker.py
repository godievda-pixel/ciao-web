from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

marker = '/* ciao-v29-score-picker-source-20260908 */'
if s.count(marker) != 1:
    raise SystemExit(f'expected exactly one duplicate picker marker, got {s.count(marker)}')

pattern = r'\n[ \t]*/\* ciao-v29-score-picker-source-20260908 \*/[\s\S]*?(?=\n[ \t]*function __cwPredExternalEditCard\(match\))'
s2, n = re.subn(pattern, '\n', s, count=1)
if n != 1:
    raise SystemExit(f'failed to remove duplicate picker source block: {n}')

# Canonical picker must remain intact.
checks = {
    'canonical marker': '<!-- ciao-v29-native-score-picker-20260908 -->' in s2,
    'canonical ensure': s2.count('function __cw29PickerEnsure(') == 1,
    'canonical open': s2.count('function __cw29PickerOpen(') == 1,
    'canonical apply': s2.count('function __cw29PickerApply(') == 1,
    'canonical id': "el.id='cw29-score-picker'" in s2,
    'canonical class': "el.className='cw29-picker'" in s2,
    'visible open css': '.cw29-picker.open{display:block}' in s2,
    'guarded handler': "root.dataset.cw29PickerBound" in s2,
    'no old picker id': 'cw28-score-picker' not in s2,
    'no old picker class': 'cw28-picker' not in s2,
    'renderer still clickable': 'data-cwpred-pick' in s2,
}
failed = [k for k, ok in checks.items() if not ok]
if failed:
    raise SystemExit('post-patch contract failed: ' + ', '.join(failed))

p.write_text(s2, encoding='utf-8')
print('removed duplicate out-of-scope picker helper; canonical cw29 picker preserved')
