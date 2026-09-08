from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

marker='ciao-v29-score-picker-source-20260908'
if marker in s:
    raise SystemExit('v29 marker already present')

# Remove the ineffective late script from v28, keep its CSS only.
pat=r'(<!-- ciao-v28-score-picker-20260908 -->\s*<style id="cw28-score-picker-style">[\s\S]*?</style>)\s*<script>[\s\S]*?</script>\s*(<!-- /ciao-v28-score-picker-20260908 -->)'
m=re.search(pat,s)
if not m:
    raise SystemExit('v28 late score-picker block not found')
s=s[:m.start()]+m.group(1)+'\n'+m.group(2)+s[m.end():]

helper=r'''
  /* ciao-v29-score-picker-source-20260908 */
  let __cw29PickerActive=null;
  function __cw29PickerEl(){
    let el=document.getElementById('cw28-score-picker');
    if(el)return el;
    el=document.createElement('div');
    el.id='cw28-score-picker';
    el.className='cw28-picker';
    el.innerHTML='<div class="cw28-picker-backdrop" data-cw28-close></div><div class="cw28-picker-panel" role="dialog" aria-modal="true"><div class="cw28-picker-title"><span>Выберите голы</span><small>0–9</small></div><div class="cw28-picker-grid">'+Array.from({length:10},(_,i)=>'<button type="button" data-cw28-score="'+i+'">'+i+'</button>').join('')+'</div></div>';
    document.body.appendChild(el);
    el.addEventListener('click',e=>{
      if(e.target.closest('[data-cw28-close]')){__cw29PickerClose();return}
      const b=e.target.closest('[data-cw28-score]');
      if(!b||!__cw29PickerActive)return;
      __cw29PickerApply(Number(b.getAttribute('data-cw28-score')));
      __cw29PickerClose();
    });
    return el;
  }
  function __cw29PickerClose(){const el=document.getElementById('cw28-score-picker');if(el)el.classList.remove('open');__cw29PickerActive=null}
  function __cw29PickerOpen(btn){
    const card=btn.closest('[data-cwpred-match],[data-mid]');
    if(!card)return;
    __cw29PickerActive={btn,card,side:String(btn.getAttribute('data-cwpred-pick')||'h'),external:card.hasAttribute('data-cwpred-match')};
    __cw29PickerEl().classList.add('open');
    try{tg?.HapticFeedback?.selectionChanged?.()}catch(_e){}
  }
  function __cw29PickerApply(n){
    const active=__cw29PickerActive;
    if(!active||!Number.isInteger(n)||n<0||n>9)return;
    const side=active.side==='a'?'a':'h';
    if(active.external){
      const key=String(active.card.getAttribute('data-cwpred-match')||'');
      const match=(__cwPredSelectedGroup()?.matches||[]).find(x=>String(x?.matchId||'')===key);
      if(!match?.open)return;
      const cur=__cwPredExternalScoreOf(match),next={h:Number(cur.h)||0,a:Number(cur.a)||0};
      next[side]=n;
      __cwPredExternalDraft.set(key,next);
      __cw26PatchExternalCard(active.card,key,next);
    }else{
      const id=Number(active.card.getAttribute('data-mid')||0),match=(S?.round?.matches||[]).find(x=>Number(x.id)===id);
      if(!match?.open)return;
      const cur=draft.get(id)||{h:Number(match?.prediction?.home_score??0),a:Number(match?.prediction?.away_score??0)},next={h:Number(cur.h)||0,a:Number(cur.a)||0};
      next[side]=n;
      draft.set(id,next);
      __cw26PatchSerieCard(active.card,id,next);
    }
    __cw26PredScheduleAutosave();
    try{tg?.HapticFeedback?.selectionChanged?.()}catch(_e){}
  }
  document.addEventListener('keydown',e=>{if(e.key==='Escape')__cw29PickerClose()});
  root.addEventListener('click',e=>{const b=e.target.closest('[data-cwpred-pick]');if(!b)return;e.preventDefault();e.stopPropagation();__cw29PickerOpen(b)});
'''

anchor='  function __cwPredExternalEditCard(match)'
pos=s.find(anchor)
if pos<0:
    raise SystemExit('active external edit renderer not found')
s=s[:pos]+helper+s[pos:]

external=r'''  function __cwPredExternalEditCard(match){const value=__cwPredExternalScoreOf(match),key=String(match?.matchId||''),dirty=__cwPredExternalDraft.has(key),saved=!!match?.prediction;const score=match?.open?'<div class="cw28-score-line"><button type="button" class="cw28-score-pick" data-cwpred-pick="h" aria-label="Голы хозяев">'+value.h+'</button><span class="cw28-score-colon">:</span><button type="button" class="cw28-score-pick" data-cwpred-pick="a" aria-label="Голы гостей">'+value.a+'</button></div>':'<div class="cwpred-locked-prediction">'+__cwPredEsc(__cwPredExternalPredictionText(match))+'</div>';return '<article class="cwpred-card cwpred-external-card '+(match?.open?'open':'closed')+'" data-cwpred-match="'+__cwPredEsc(key)+'"><div class="cwpred-card-top"><span class="cwpred-status">'+__cwPredEsc(__cwPredStatus(match))+'</span><span class="cwpred-kickoff">'+__cwPredEsc(__cwPredDateTime(match?.kickoffAt))+'</span></div><div class="cwpred-card-main">'+__cwPredExternalTeamHtml(match?.homeTeam,'home')+'<div class="cwpred-score-zone">'+score+'<div class="cwpred-save-state '+(dirty?'dirty':saved?'saved':'')+'">'+(dirty?'Изменено':saved?'✓ Сохранено':match?.open?'Нажмите на счёт':'Прогноз не сделан')+'</div></div>'+__cwPredExternalTeamHtml(match?.awayTeam,'away')+'</div><div class="cwpred-card-bottom"><span>'+__cwPredEsc(__cwPredDeadlineText(match))+'</span>'+(__cwPredRealScore(match)?'<span>'+__cwPredEsc(__cwPredRealScore(match))+'</span>':'')+'</div></article>'}
'''
s,n=re.subn(r'  function __cwPredExternalEditCard\(match\)\{[\s\S]*?\n  function __cwPredExternalMineCard',external+'  function __cwPredExternalMineCard',s,count=1)
if n!=1:
    raise SystemExit(f'expected one external renderer replacement, got {n}')

serie=r'''  function __cwPredSerieEditCard(match){const v=scoreOf(match),saved=!!match?.prediction,dirty=draft.has(Number(match.id));const score=match.open?'<div class="cw28-score-line"><button type="button" class="cw28-score-pick" data-cwpred-pick="h" aria-label="Голы хозяев">'+v.h+'</button><span class="cw28-score-colon">:</span><button type="button" class="cw28-score-pick" data-cwpred-pick="a" aria-label="Голы гостей">'+v.a+'</button></div>':'<div class="cwpred-locked-prediction">'+(saved?String(match.prediction.home_score)+' : '+String(match.prediction.away_score):'Прогноз не сделан')+'</div>';return '<div class="match cwpred-card cwpred-serie-card '+(match.open?'open':'closed')+'" data-mid="'+Number(match.id)+'"><div class="cwpred-card-top"><span class="cwpred-status">'+__cwPredEsc(__cwPredSerieStatus(match))+'</span><span class="cwpred-kickoff">'+__cwPredEsc(typeof fmt==='function'?fmt(match.kickoff_at):'')+'</span></div><div class="cwpred-card-main">'+__cwPredSerieTeamHtml(match.home,'home')+'<div class="cwpred-score-zone">'+score+'<div class="cwpred-save-state '+(dirty?'dirty':saved?'saved':'')+'">'+(dirty?'Изменено':saved?'✓ Сохранено':match.open?'Нажмите на счёт':'Прогноз не сделан')+'</div></div>'+__cwPredSerieTeamHtml(match.away,'away')+'</div><div class="cwpred-card-bottom"><span>'+(match.open?'Дедлайн за 15 минут до начала':'Прогноз закрыт')+'</span>'+(__cwPredSerieRealScore(match)?'<span>'+__cwPredEsc(__cwPredSerieRealScore(match))+'</span>':'')+'</div></div>'}
'''
s,n=re.subn(r'  function __cwPredSerieEditCard\(match\)\{[\s\S]*?\n  function __cwPredSerieMineCard',serie+'  function __cwPredSerieMineCard',s,count=1)
if n!=1:
    raise SystemExit(f'expected one serie renderer replacement, got {n}')

old_ext="  function __cw26PatchExternalCard(card,key,v){const x=card?.querySelectorAll?.('.cwpred-score-side b')||[];if(x[0])x[0].textContent=String(v.h);if(x[1])x[1].textContent=String(v.a);__cw26PredSetState('external',key,'dirty')}"
new_ext="  function __cw26PatchExternalCard(card,key,v){const h=card?.querySelector?.('.cw28-score-pick[data-cwpred-pick=\"h\"]'),a=card?.querySelector?.('.cw28-score-pick[data-cwpred-pick=\"a\"]');if(h)h.textContent=String(v.h);if(a)a.textContent=String(v.a);__cw26PredSetState('external',key,'dirty')}"
if s.count(old_ext)!=1:
    raise SystemExit(f'expected one external patch helper, got {s.count(old_ext)}')
s=s.replace(old_ext,new_ext,1)

old_ser="  function __cw26PatchSerieCard(card,id,v){const x=card?.querySelectorAll?.('.cwpred-score-side .score-value')||[],h=card?.querySelector?.('[data-score-side=\"h\"]')||x[0],a=card?.querySelector?.('[data-score-side=\"a\"]')||x[1];if(h)h.textContent=String(v.h);if(a)a.textContent=String(v.a);__cw26PredSetState('serie',id,'dirty')}"
new_ser="  function __cw26PatchSerieCard(card,id,v){const h=card?.querySelector?.('.cw28-score-pick[data-cwpred-pick=\"h\"]'),a=card?.querySelector?.('.cw28-score-pick[data-cwpred-pick=\"a\"]');if(h)h.textContent=String(v.h);if(a)a.textContent=String(v.a);__cw26PredSetState('serie',id,'dirty')}"
if s.count(old_ser)!=1:
    raise SystemExit(f'expected one serie patch helper, got {s.count(old_ser)}')
s=s.replace(old_ser,new_ser,1)

# Prediction tab must not be periodically full-rendered.
guard="if(tab==='predict'||tab==='mine')return false;"
if guard not in s:
    raise SystemExit('prediction refresh guard missing')

p.write_text(s,encoding='utf-8')
