#!/usr/bin/env python3
from pathlib import Path
import re, sys

P=Path('index.html')
MARK='cw27-android-predictions-style'

def fail(msg):
    print(msg, file=sys.stderr); raise SystemExit(1)

def region(s,a,b):
    i=s.rfind(a)
    if i<0: fail('missing '+a)
    j=s.find(b,i+len(a))
    if j<0: fail('missing next anchor '+b)
    return s[i:j]

def red(s):
    ext=region(s,'function __cwPredExternalTeamHtml(team,side)','function __cwPredSerieTeamHtml(team,side)')
    ser=region(s,'function __cwPredSerieTeamHtml(team,side)','function __cwPredDateTime(value)')
    bind=region(s,'function __cwPredBindExternal()','function __cwPredBind(){')
    if MARK in s: fail('RED expected style marker absent')
    if 'data-cwpred-local-club' not in ext or 'data-cwpred-local-club' not in ser: fail('RED expected clickable club markup')
    if "querySelectorAll('[data-cwpred-local-club]')" not in bind: fail('RED expected club-profile click binding')
    if '@media(max-width:390px)' not in s: fail('RED expected old 390px mobile breakpoint')
    print('RED PASS: Android overflow/click-through behavior still present')

def green(s):
    ext=region(s,'function __cwPredExternalTeamHtml(team,side)','function __cwPredSerieTeamHtml(team,side)')
    ser=region(s,'function __cwPredSerieTeamHtml(team,side)','function __cwPredDateTime(value)')
    bind=region(s,'function __cwPredBindExternal()','function __cwPredBind(){')
    if MARK not in s: fail('GREEN missing Android style marker')
    if 'data-cwpred-local-club' in ext or 'data-cwpred-local-club' in ser: fail('GREEN predictor team markup is still clickable')
    if '<button' in ext or '<button' in ser: fail('GREEN predictor team is still rendered as a button')
    if 'data-cwpred-local-club' in bind or 'openClubProfile' in bind: fail('GREEN club-profile click binding still active in predictions')
    style=region(s,f'<style id="{MARK}">','</style>')
    for token in ['@media(max-width:520px)', 'grid-template-columns:minmax(82px,1fr) 166px minmax(82px,1fr)', 'width:28px!important', 'touch-action:manipulation']:
        if token not in style: fail('GREEN missing responsive token: '+token)
    print('GREEN PASS: prediction controls are Android-responsive and club clicks are disabled')

def replace_region(s,a,b,new):
    i=s.rfind(a)
    if i<0: fail('patch missing '+a)
    j=s.find(b,i+len(a))
    if j<0: fail('patch missing next '+b)
    return s[:i]+new+s[j:]

def patch(s):
    if MARK in s: fail('already patched')
    ext="""function __cwPredExternalTeamHtml(team,side){const crest=String(team?.crestUrl||'').trim(),body=(crest?'<img class=\\\"cwpred-team-logo\\\" loading=\\\"lazy\\\" decoding=\\\"async\\\" src=\\\"'+__cwPredEsc(crest)+'\\\" alt=\\\"\\\">':'<span class=\\\"cwpred-team-logo cwpred-team-logo--empty\\\"></span>')+'<span class=\\\"cwpred-team-name\\\">'+__cwPredEsc(team?.name||'—')+'</span>';return '<div class=\\\"cwpred-team cwpred-team--'+side+'\\\">'+body+'</div>'}\n  """
    ser="""function __cwPredSerieTeamHtml(team,side){const body=(typeof logo==='function'?logo(team):'')+'<span class=\\\"cwpred-team-name\\\">'+__cwPredEsc(team?.name||'—')+'</span>';return '<div class=\\\"cwpred-team cwpred-team--'+side+'\\\">'+body+'</div>'}\n  """
    bind="""function __cwPredBindExternal(){\n    root.querySelectorAll('[data-cwpred-delta]').forEach(btn=>btn.addEventListener('click',()=>{const host=btn.closest('[data-cwpred-match]'),key=String(host?.getAttribute('data-cwpred-match')||''),match=(__cwPredSelectedGroup()?.matches||[]).find(row=>String(row?.matchId||'')===key);if(!match?.open)return;const current=__cwPredExternalScoreOf(match),parts=String(btn.getAttribute('data-cwpred-delta')||'').split(':'),side=parts[0],delta=Number(parts[1]),next={h:current.h,a:current.a};if(side!=='h'&&side!=='a')return;next[side]=Math.max(0,Math.min(20,Number(next[side]||0)+delta));__cwPredExternalDraft.set(key,next);__cw26PatchExternalCard(host,key,next);__cw26PredScheduleAutosave()}));\n  }\n  """
    s=replace_region(s,'function __cwPredExternalTeamHtml(team,side)','function __cwPredSerieTeamHtml(team,side)',ext)
    s=replace_region(s,'function __cwPredSerieTeamHtml(team,side)','function __cwPredDateTime(value)',ser)
    s=replace_region(s,'function __cwPredBindExternal()','function __cwPredBind(){',bind)
    style='''\n<style id="cw27-android-predictions-style">\n/* Ciao v27 — Android prediction controls + no club click-through */\n#ciao-miniapp-root .cwpred-team{cursor:default!important;user-select:none;-webkit-user-select:none}\n@media(max-width:520px){\n#ciao-miniapp-root .cwpred-card{padding:11px 9px 10px!important;border-radius:18px!important}\n#ciao-miniapp-root .cwpred-card-main{grid-template-columns:minmax(82px,1fr) 166px minmax(82px,1fr)!important;gap:2px!important}\n#ciao-miniapp-root .cwpred-score-zone{width:166px!important;max-width:166px!important}\n#ciao-miniapp-root .cwpred-score{width:100%!important;gap:2px!important}\n#ciao-miniapp-root .cwpred-score-side{grid-template-columns:28px 18px 28px!important;gap:1px!important}\n#ciao-miniapp-root .cwpred-score-side button{min-width:28px!important;width:28px!important;height:38px!important;padding:0!important;border-radius:10px!important;font-size:18px!important;line-height:1!important;touch-action:manipulation}\n#ciao-miniapp-root .cwpred-score-side b,#ciao-miniapp-root .cwpred-score-side .score-value{min-width:18px!important;width:18px!important;font-size:18px!important;line-height:38px!important}\n#ciao-miniapp-root .cwpred-score>span,#ciao-miniapp-root .cwpred-score .colon{width:10px!important;font-size:15px!important;text-align:center!important}\n#ciao-miniapp-root .cwpred-team-logo,#ciao-miniapp-root .cwpred-team .logo{width:40px!important;height:40px!important;max-width:40px!important;flex:0 0 40px!important}\n#ciao-miniapp-root .cwpred-team-name{font-size:10.5px!important;line-height:1.12!important}\n#ciao-miniapp-root .cwpred-rounds .round-chip{min-width:40px!important;height:38px!important;padding:0 10px!important}\n}\n@media(max-width:390px){\n#ciao-miniapp-root .cwpred-card-main{grid-template-columns:minmax(74px,1fr) 154px minmax(74px,1fr)!important;gap:1px!important}\n#ciao-miniapp-root .cwpred-score-zone{width:154px!important;max-width:154px!important}\n#ciao-miniapp-root .cwpred-score-side{grid-template-columns:26px 17px 26px!important}\n#ciao-miniapp-root .cwpred-score-side button{min-width:26px!important;width:26px!important;height:36px!important;font-size:17px!important}\n#ciao-miniapp-root .cwpred-score-side b,#ciao-miniapp-root .cwpred-score-side .score-value{min-width:17px!important;width:17px!important;font-size:17px!important;line-height:36px!important}\n#ciao-miniapp-root .cwpred-team-logo,#ciao-miniapp-root .cwpred-team .logo{width:38px!important;height:38px!important;max-width:38px!important;flex:0 0 38px!important}\n#ciao-miniapp-root .cwpred-team-name{font-size:10px!important}\n}\n</style>\n'''
    if '</head>' not in s: fail('missing </head>')
    return s.replace('</head>',style+'</head>',1)

def main():
    s=P.read_text(encoding='utf-8')
    mode=sys.argv[1] if len(sys.argv)>1 else 'red'
    if mode=='red': red(s)
    elif mode=='patch': P.write_text(patch(s),encoding='utf-8'); print('PATCH APPLIED')
    elif mode=='green': green(s)
    else: fail('usage: red|patch|green')

if __name__=='__main__': main()
