from pathlib import Path
import re
import subprocess

p = Path('index.html')
s = p.read_text()
marker = 'ciao-premium-italy-loading-system-20260909'

# RED: the shared system must not exist before this patch.
if marker in s:
    raise SystemExit('RED unexpectedly passed: shared premium loading system already exists')
print('RED failed as expected: shared premium loading system marker is absent')

replacements = {
    'class=\\"cwpred-state\\">Загружаем прогнозы…': 'class=\\"cwpred-state cw-it-loading\\">Загружаем прогнозы…',
    'class=\\"cwpred-state\\">Загружаем тур…': 'class=\\"cwpred-state cw-it-loading\\">Загружаем тур…',
    'class=\\"cwpred-state\\">Обновляем Главную…': 'class=\\"cwpred-state cw-it-loading\\">Обновляем Главную…',
    'class=\\"cwmt-state\\">Загружаем матчи…': 'class=\\"cwmt-state cw-it-loading\\">Загружаем матчи…',
}
seen = {}
for old, new in replacements.items():
    n = s.count(old)
    seen[old] = n
    if n:
        s = s.replace(old, new)

assert seen['class=\\"cwpred-state\\">Загружаем прогнозы…'] >= 1
assert seen['class=\\"cwpred-state\\">Загружаем тур…'] >= 1
assert seen['class=\\"cwmt-state\\">Загружаем матчи…'] >= 1

css = r'''
<style id="ciao-premium-italy-loading-system">
/* ciao-premium-italy-loading-system-20260909 */
@keyframes cwItSweep{
  0%{transform:translateX(-115%);opacity:.68}
  46%,62%{transform:translateX(72%);opacity:1}
  100%{transform:translateX(220%);opacity:.72}
}
@keyframes cwItCompact{
  0%{background-position:120% 50%;opacity:.72}
  50%{opacity:1}
  100%{background-position:-20% 50%;opacity:.72}
}
#ciao-miniapp-root .loader{min-height:45vh!important}
#ciao-miniapp-root .loader-box{gap:12px!important}
#ciao-miniapp-root .loader-mark{
  position:relative!important;width:min(44vw,154px)!important;height:7px!important;min-height:7px!important;
  aspect-ratio:auto!important;overflow:hidden!important;border-radius:999px!important;
  border:1px solid rgba(255,255,255,.10)!important;background:rgba(255,255,255,.05)!important;
  box-shadow:0 10px 28px rgba(0,0,0,.26),inset 0 1px 0 rgba(255,255,255,.07)!important;
}
#ciao-miniapp-root .loader-mark::before{
  content:''!important;position:absolute!important;inset:1px auto 1px 0!important;width:58%!important;height:auto!important;
  -webkit-mask:none!important;mask:none!important;border-radius:999px!important;
  background:linear-gradient(90deg,#008C45 0 33.333%,#f5f5f0 33.333% 66.666%,#CD212A 66.666% 100%)!important;
  background-size:100% 100%!important;background-position:center!important;
  animation:cwItSweep 1.45s cubic-bezier(.55,.05,.45,.95) infinite!important;
  filter:none!important;clip-path:none!important;opacity:1!important;
}
#ciao-miniapp-root .loader-mark::after{
  content:''!important;display:block!important;position:absolute!important;inset:1px!important;border-radius:999px!important;
  background:linear-gradient(180deg,rgba(255,255,255,.20),transparent 55%)!important;
  filter:none!important;animation:none!important;pointer-events:none!important;
}
#ciao-miniapp-root .loader-title{font-size:16px!important}
#ciao-miniapp-root .loader-sub{font-size:10px!important;color:#8494bb!important;max-width:240px}
#ciao-miniapp-root .cw-it-loading,
#ciao-miniapp-root .cw16-club-loading,
#ciao-miniapp-root .cw209-calendar-loading{
  display:flex!important;flex-direction:column!important;align-items:center!important;justify-content:center!important;
  gap:12px!important;text-align:center!important;
}
#ciao-miniapp-root .cw-it-loading::after,
#ciao-miniapp-root .cw16-club-loading::after,
#ciao-miniapp-root .cw209-calendar-loading::after{
  content:'';display:block;width:min(42vw,146px);height:5px;border-radius:999px;
  background:linear-gradient(90deg,transparent 0%,#008C45 20%,#f5f5f0 50%,#CD212A 80%,transparent 100%);
  background-size:220% 100%;background-position:120% 50%;animation:cwItCompact 1.35s ease-in-out infinite;
  box-shadow:0 0 12px rgba(255,255,255,.08);opacity:.95;
}
#ciao-miniapp-root .cw18-skeleton::after,
#ciao-miniapp-root .cw30-rating-state i::after,
#ciao-miniapp-root .cw31-profile-skeleton i::after,
#ciao-miniapp-root .mc-lazy-loading::after,
#ciao-miniapp-root .cw22-sk::after{
  background:linear-gradient(90deg,transparent 0%,rgba(0,140,69,.11) 30%,rgba(255,255,255,.12) 50%,rgba(205,33,42,.11) 70%,transparent 100%)!important;
}
@media(prefers-reduced-motion:reduce){
  #ciao-miniapp-root .loader-mark::before,
  #ciao-miniapp-root .cw-it-loading::after,
  #ciao-miniapp-root .cw16-club-loading::after,
  #ciao-miniapp-root .cw209-calendar-loading::after{animation:none!important;transform:none!important;background-position:50% 50%!important}
}
</style>
'''
assert '</head>' in s
s = s.replace('</head>', css + '\n</head>', 1)
p.write_text(s)

# GREEN contract.
s = p.read_text()
assert s.count(marker) == 1
assert '@keyframes cwItSweep' in s and '@keyframes cwItCompact' in s
assert '#008C45' in s and '#CD212A' in s
assert 'cwpred-state cw-it-loading\\">Загружаем прогнозы…' in s
assert 'cwpred-state cw-it-loading\\">Загружаем тур…' in s
assert 'cwmt-state cw-it-loading\\">Загружаем матчи…' in s
assert '#ciao-miniapp-root .cw16-club-loading::after' in s
assert '#ciao-miniapp-root .cw209-calendar-loading::after' in s
assert '#ciao-miniapp-root .cw30-rating-state i::after' in s
assert '#ciao-miniapp-root .cw31-profile-skeleton i::after' in s
assert '#ciao-miniapp-root .mc-lazy-loading::after' in s
assert 'ciao-premium-italy-loader-20260909' in s
assert 'ciao-v29-native-score-picker-20260908' in s
print('GREEN: shared premium loading contract satisfied')

# Syntax verification for every inline JS script.
scripts = re.findall(r'<script([^>]*)>(.*?)</script>', s, re.S | re.I)
checked = 0
for i, (attrs, js) in enumerate(scripts):
    a = attrs.lower()
    if 'src=' in a or ('type=' in a and 'javascript' not in a and 'module' not in a):
        continue
    if not js.strip():
        continue
    f = Path(f'/tmp/ciao-inline-{i}.js')
    f.write_text(js)
    subprocess.run(['node', '--check', str(f)], check=True)
    checked += 1
print(f'node --check OK for {checked} inline scripts')
