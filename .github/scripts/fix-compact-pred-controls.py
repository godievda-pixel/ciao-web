from pathlib import Path
import re, sys, subprocess, tempfile, os

P=Path('index.html')
STYLE_ID='cw27-android-predictions-style'
NEW_STYLE='''<style id="cw27-android-predictions-style">
/* Ciao v27.1 — compact prediction controls on phones + no club click-through */
#ciao-miniapp-root .cwpred-team{cursor:default!important;user-select:none;-webkit-user-select:none}
@media(max-width:520px){
#ciao-miniapp-root .cwpred-card{padding:11px 9px 10px!important;border-radius:18px!important}
#ciao-miniapp-root .cwpred-card-main{grid-template-columns:minmax(82px,1fr) 158px minmax(82px,1fr)!important;gap:2px!important}
#ciao-miniapp-root .cwpred-score{gap:2px!important}
#ciao-miniapp-root .cwpred-score-side{grid-template-columns:26px 20px 26px!important;gap:1px!important}
#ciao-miniapp-root .cwpred-score-side button{min-width:26px!important;width:26px!important;height:34px!important;padding:0!important;border-radius:10px!important;font-size:17px!important;touch-action:manipulation!important}
#ciao-miniapp-root .cwpred-score-side b,#ciao-miniapp-root .cwpred-score-side .score-value{min-width:20px!important;font-size:18px!important}
#ciao-miniapp-root .cwpred-score>span,#ciao-miniapp-root .cwpred-score .colon{font-size:15px!important}
}
@media(max-width:390px){
#ciao-miniapp-root .cwpred-card-main{grid-template-columns:minmax(74px,1fr) 148px minmax(74px,1fr)!important;gap:1px!important}
#ciao-miniapp-root .cwpred-score{gap:1px!important}
#ciao-miniapp-root .cwpred-score-side{grid-template-columns:24px 18px 24px!important;gap:1px!important}
#ciao-miniapp-root .cwpred-score-side button{min-width:24px!important;width:24px!important;height:32px!important;border-radius:9px!important;font-size:16px!important}
#ciao-miniapp-root .cwpred-score-side b,#ciao-miniapp-root .cwpred-score-side .score-value{min-width:18px!important;font-size:17px!important}
}
</style>'''

def block(s):
    m=re.search(r'<style id="'+re.escape(STYLE_ID)+r'">[\s\S]*?</style>',s)
    if not m:
        raise SystemExit('style block not found')
    return m.group(0)

def test():
    s=P.read_text()
    b=block(s)
    checks=[
        ' 158px ' in b,
        'grid-template-columns:26px 20px 26px!important' in b,
        'width:26px!important;height:34px!important' in b,
        ' 148px ' in b,
        'grid-template-columns:24px 18px 24px!important' in b,
        'width:24px!important;height:32px!important' in b,
        ' 166px ' not in b,
    ]
    if not all(checks):
        print('compact prediction controls contract NOT satisfied')
        sys.exit(1)
    # Keep the no-click-through behavior introduced in v27.
    if 'data-cwpred-local-club' in b:
        print('unexpected click-through marker in style block')
        sys.exit(1)
    print('compact prediction controls contract satisfied')

def patch():
    s=P.read_text()
    old=block(s)
    if ' 166px ' not in old:
        raise SystemExit('expected old 166px center not found; refusing ambiguous patch')
    s=s.replace(old,NEW_STYLE,1)
    P.write_text(s)
    print('patched cw27 style block')

def check_js():
    s=P.read_text()
    scripts=re.findall(r'<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)</script>',s,flags=re.I)
    if not scripts:
        raise SystemExit('no inline scripts found')
    for i,code in enumerate(scripts):
        fd,path=tempfile.mkstemp(suffix='.js')
        os.close(fd)
        try:
            Path(path).write_text(code)
            r=subprocess.run(['node','--check',path],capture_output=True,text=True)
            if r.returncode:
                print(r.stdout); print(r.stderr,file=sys.stderr); raise SystemExit(f'inline JS block {i} failed')
        finally:
            try: os.unlink(path)
            except OSError: pass
    print(f'inline JS syntax OK ({len(scripts)} blocks)')

mode=sys.argv[1] if len(sys.argv)>1 else '--test'
{'--test':test,'--patch':patch,'--check-js':check_js}.get(mode,lambda:(_ for _ in ()).throw(SystemExit('bad mode')))()
