from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

if 'ciao-v29-native-score-picker-20260908' in s:
    raise SystemExit('cw29 marker already present')

# Remove the ineffective out-of-scope cw28 injection completely.
s,n=re.subn(r'\n*<!-- ciao-v28-score-picker-20260908 -->[\s\S]*?<!-- /ciao-v28-score-picker-20260908 -->\s*', '\n', s, count=1)
if n != 1:
    raise SystemExit(f'expected one cw28 block, removed {n}')

style=r'''
<!-- ciao-v29-native-score-picker-20260908 -->
<style id="cw29-score-picker-style">
#ciao-miniapp-root .cwpred-card-main{grid-template-columns:minmax(0,1fr) 92px minmax(0,1fr)!important;gap:6px!important}
#ciao-miniapp-root .cw29-score-line{display:grid;grid-template-columns:38px 10px 38px;align-items:center;justify-content:center;gap:3px;margin:0 auto}
#ciao-miniapp-root .cw29-score-pick{appearance:none;width:38px;height:36px;padding:0;border:1px solid rgba(255,255,255,.13);border-radius:11px;background:linear-gradient(180deg,rgba(255,255,255,.09),rgba(255,255,255,.045));color:#fff;font:950 19px/1 'Manrope',sans-serif;box-shadow:inset 0 1px 0 rgba(255,255,255,.08);touch-action:manipulation}
#ciao-miniapp-root .cw29-score-pick:active{transform:scale(.96);background:rgba(var(--cwpred-a-rgb,49,80,255),.20)}
#ciao-miniapp-root .cw29-score-colon{color:rgba(255,255,255,.66);font-size:16px;font-weight:900;text-align:center}
.cw29-picker{position:fixed;inset:0;z-index:2147483000;display:none;pointer-events:none}
.cw29-picker.open{display:block}
.cw29-picker-backdrop{position:absolute;inset:0;background:rgba(1,5,16,.22);pointer-events:auto}
.cw29-picker-panel{position:absolute;left:12px;right:12px;bottom:calc(84px + env(safe-area-inset-bottom,0px));max-width:360px;margin:auto;padding:12px;border:1px solid rgba(135,155,255,.20);border-radius:20px;background:rgba(7,14,36,.98);box-shadow:0 22px 65px rgba(0,0,0,.48),inset 0 1px 0 rgba(255,255,255,.06);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);pointer-events:auto}
.cw29-picker-title{display:flex;align-items:center;justify-content:space-between;margin:0 2px 10px;color:#fff;font:800 12px/1.2 'Manrope',sans-serif}
.cw29-picker-title small{color:rgba(255,255,255,.45);font-size:10px;font-weight:700}
.cw29-picker-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:7px}
.cw29-picker-grid button{height:43px;border:1px solid rgba(255,255,255,.09);border-radius:13px;background:rgba(255,255,255,.055);color:#fff;font:900 16px/1 'Manrope',sans-serif;touch-action:manipulation}
.cw29-picker-grid button:active{transform:scale(.96);background:rgba(49,80,255,.25);border-color:rgba(116,139,255,.36)}
@media(max-width:390px){
#ciao-miniapp-root .cwpred-card-main{grid-template-columns:minmax(0,1fr) 84px minmax(0,1fr)!important;gap:4px!important}
#ciao-miniapp-root .cw29-score-line{grid-template-columns:35px 8px 35px;gap:2px}
#ciao-miniapp-root .cw29-score-pick{width:35px;height:34px;border-radius:10px;font-size:18px}
.cw29-picker-panel{left:9px;right:9px;padding:10px;border-radius:18px}
.cw29-picker-grid{gap:6px}
.cw29-picker-grid button{height:40px;border-radius:12px;font-size:15px}
}
</style>
<!-- /ciao-v29-native-score-picker-20260908 -->
'''
if '</head>' not in s:
    raise SystemExit('missing </head>')
s=s.replace('</head>', style+'\n</head>', 1)

helper=r'''
  let __cw29PickerActive=null;
  function __cw29PickerEnsure(){
    let el=document.getElementById('cw29-score-picker');
    if(el)return el;
    el=document.createElement('div');
    el.id='cw29-score-picker';
    el.className='cw29-picker';
    el.innerHTML='<div class="cw29-picker-backdrop" data-cw29-close></div><div class="cw29-picker-panel" role="dialog" aria-modal="true"><div class="cw29-picker-title"><span>Выберите голы</span><small>0–9</small></div><div class="cw29-picker-grid">'+Array.from({length:10},(_,i)=>'<button type="button" data-cw29-score="'+i+'">'+i+'</button>').join('')+'</div></div>';
    document.body.appendChild(el);
    el.addEventListener('click',e=>{
      if(e.target.closest('[data-cw29-close]')){__cw29PickerClose();return}
      const b=e.target.closest('[data-cw29-score]');
      if(!b||!__cw29PickerActive)return;
      __cw29PickerApply(Number(b.getAttribute('data-cw29-score')));
      __cw29PickerClose();
    });
    return el;
  }
  function __cw29PickerClose(){const el=document.getElementById('cw29-score-picker');if(el)el.classList.remove('open');__cw29PickerActive=null}
  function __cw29PickerOpen(btn){
    const card=btn.closest('[data-cwpred-match],[data-mid]');
    if(!card)return;
    __cw29PickerActive={btn,card,side:String(btn.getAttribute('data-cwpred-pick')||'h'),external:card.hasAttribute('data-cwpred-match')};
    __cw29PickerEnsure().classList.add('open');
    try{tg?.HapticFeedback?.selectionChanged?.()}catch(_e){}
  }
  function __cw29PickerApply(n){
    if(!__cw29PickerActive||!Number.isInteger(n)||n<0||n>9)return;
    const x=__cw29PickerActive,side=x.side==='a'?'a':'h';
    if(x.external){
      const key=String(x.card.getAttribute('data-cwpred-match')||''),match=(__cwPredSelectedGroup()?.matches||[]).find(row=>String(row?.matchId||'')===key);
      if(!match?.open)return;
      const cur=__cwPredExternalScoreOf(match),next={h:Number(cur.h)||0,a:Number(cur.a)||0};
      next[side]=n;__cwPredExternalDraft.set(key,next);__cw26PatchExternalCard(x.card,key,next);
    }else{
      const id=Number(x.card.getAttribute('data-mid')||0),match=(S?.round?.matches||[]).find(row=>Number(row.id)===id);
      if(!match?.open)return;
      const cur=draft.get(id)||{h:Number(match?.prediction?.home_score??0),a:Number(match?.prediction?.away_score??0)},next={h:Number(cur.h)||0,a:Number(cur.a)||0};
      next[side]=n;draft.set(id,next);__cw26PatchSerieCard(x.card,id,next);
    }
    __cw26PredScheduleAutosave();
    try{tg?.HapticFeedback?.selectionChanged?.()}catch(_e){}
  }
  root.addEventListener('click',e=>{const b=e.target.closest('[data-cwpred-pick]');if(!b)return;e.preventDefault();e.stopPropagation();__cw29PickerOpen(b)});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')__cw29PickerClose()});

'''
anchor='  function __cwPredRealScore(match)'
if s.count(anchor) != 1:
    raise SystemExit(f'expected one score anchor, got {s.count(anchor)}')
s=s.replace(anchor, helper+anchor, 1)

external_new="""  function __cwPredExternalEditCard(match){const value=__cwPredExternalScoreOf(match),key=String(match?.matchId||''),dirty=__cwPredExternalDraft.has(key),saved=!!match?.prediction;const score=match?.open?'<div class=\\\"cw29-score-line\\\"><button type=\\\"button\\\" class=\\\"cw29-score-pick\\\" data-cwpred-pick=\\\"h\\\" aria-label=\\\"Голы хозяев\\\">'+value.h+'</button><span class=\\\"cw29-score-colon\\\">:</span><button type=\\\"button\\\" class=\\\"cw29-score-pick\\\" data-cwpred-pick=\\\"a\\\" aria-label=\\\"Голы гостей\\\">'+value.a+'</button></div>':'<div class=\\\"cwpred-locked-prediction\\\">'+__cwPredEsc(__cwPredExternalPredictionText(match))+'</div>';return '<article class=\\\"cwpred-card cwpred-external-card '+(match?.open?'open':'closed')+'\\\" data-cwpred-match=\\\"'+__cwPredEsc(key)+'\\\"><div class=\\\"cwpred-card-top\\\"><span class=\\\"cwpred-status\\\">'+__cwPredEsc(__cwPredStatus(match))+'</span><span class=\\\"cwpred-kickoff\\\">'+__cwPredEsc(__cwPredDateTime(match?.kickoffAt))+'</span></div><div class=\\\"cwpred-card-main\\\">'+__cwPredExternalTeamHtml(match?.homeTeam,'home')+'<div class=\\\"cwpred-score-zone\\\">'+score+'<div class=\\\"cwpred-save-state '+(dirty?'dirty':saved?'saved':'')+'\\\">'+(dirty?'Изменено':saved?'✓ Сохранено':match?.open?'Нажмите на счёт':'Прогноз не сделан')+'</div></div>'+__cwPredExternalTeamHtml(match?.awayTeam,'away')+'</div><div class=\\\"cwpred-card-bottom\\\"><span>'+__cwPredEsc(__cwPredDeadlineText(match))+'</span>'+( __cwPredRealScore(match)?'<span>'+__cwPredEsc(__cwPredRealScore(match))+'</span>':'')+'</div></article>'}"""
s,n=re.subn(r'^  function __cwPredExternalEditCard\(match\)\{[^\n]*$', external_new, s, count=1, flags=re.M)
if n != 1:
    raise SystemExit(f'failed to replace active external edit card: {n}')

serie_new="""  function __cwPredSerieEditCard(match){const v=scoreOf(match),saved=!!match?.prediction,dirty=draft.has(Number(match.id));const score=match.open?'<div class=\\\"cw29-score-line\\\"><button type=\\\"button\\\" class=\\\"cw29-score-pick\\\" data-cwpred-pick=\\\"h\\\" aria-label=\\\"Голы хозяев\\\">'+v.h+'</button><span class=\\\"cw29-score-colon\\\">:</span><button type=\\\"button\\\" class=\\\"cw29-score-pick\\\" data-cwpred-pick=\\\"a\\\" aria-label=\\\"Голы гостей\\\">'+v.a+'</button></div>':'<div class=\\\"cwpred-locked-prediction\\\">'+(saved?String(match.prediction.home_score)+' : '+String(match.prediction.away_score):'Прогноз не сделан')+'</div>';return '<div class=\\\"match cwpred-card cwpred-serie-card '+(match.open?'open':'closed')+'\\\" data-mid=\\\"'+Number(match.id)+'\\\"><div class=\\\"cwpred-card-top\\\"><span class=\\\"cwpred-status\\\">'+__cwPredEsc(__cwPredSerieStatus(match))+'</span><span class=\\\"cwpred-kickoff\\\">'+__cwPredEsc(typeof fmt==='function'?fmt(match.kickoff_at):'')+'</span></div><div class=\\\"cwpred-card-main\\\">'+__cwPredSerieTeamHtml(match.home,'home')+'<div class=\\\"cwpred-score-zone\\\">'+score+'<div class=\\\"cwpred-save-state '+(dirty?'dirty':saved?'saved':'')+'\\\">'+(dirty?'Изменено':saved?'✓ Сохранено':match.open?'Нажмите на счёт':'Прогноз не сделан')+'</div></div>'+__cwPredSerieTeamHtml(match.away,'away')+'</div><div class=\\\"cwpred-card-bottom\\\"><span>'+(match.open?'Дедлайн за 15 минут до начала':'Прогноз закрыт')+'</span>'+( __cwPredSerieRealScore(match)?'<span>'+__cwPredEsc(__cwPredSerieRealScore(match))+'</span>':'')+'</div></div>'}"""
s,n=re.subn(r'^  function __cwPredSerieEditCard\(match\)\{[^\n]*$', serie_new, s, count=1, flags=re.M)
if n != 1:
    raise SystemExit(f'failed to replace active serie edit card: {n}')

s=s.replace(".cw28-score-pick[data-cwpred-pick=\"h\"]", ".cw29-score-pick[data-cwpred-pick=\"h\"]")
s=s.replace(".cw28-score-pick[data-cwpred-pick=\"a\"]", ".cw29-score-pick[data-cwpred-pick=\"a\"]")

p.write_text(s,encoding='utf-8')
