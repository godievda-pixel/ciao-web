from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='ciao-v28-score-picker-20260908'
if marker in s:
    raise SystemExit('marker already present')
old="if(tab==='predict')return false;"
new="if(tab==='predict'||tab==='mine')return false;"
if s.count(old)!=1:
    raise SystemExit(f'expected one Home refresh guard, got {s.count(old)}')
s=s.replace(old,new,1)

patch=r'''
<!-- ciao-v28-score-picker-20260908 -->
<style id="cw28-score-picker-style">
#ciao-miniapp-root .cwpred-card-main{grid-template-columns:minmax(0,1fr) 96px minmax(0,1fr)!important;gap:6px!important}
#ciao-miniapp-root .cw28-score-line{display:grid;grid-template-columns:40px 10px 40px;align-items:center;justify-content:center;gap:3px;margin:0 auto}
#ciao-miniapp-root .cw28-score-pick{appearance:none;width:40px;height:38px;padding:0;border:1px solid rgba(255,255,255,.13);border-radius:12px;background:linear-gradient(180deg,rgba(255,255,255,.09),rgba(255,255,255,.045));color:#fff;font:950 19px/1 'Manrope',sans-serif;box-shadow:inset 0 1px 0 rgba(255,255,255,.08);touch-action:manipulation}
#ciao-miniapp-root .cw28-score-pick:active{transform:scale(.96);background:rgba(var(--cwpred-a-rgb,49,80,255),.20)}
#ciao-miniapp-root .cw28-score-colon{color:rgba(255,255,255,.66);font-size:16px;font-weight:900;text-align:center}
.cw28-picker{position:fixed;inset:0;z-index:2147483000;display:none;pointer-events:none}
.cw28-picker.open{display:block}
.cw28-picker-backdrop{position:absolute;inset:0;background:rgba(1,5,16,.18);pointer-events:auto}
.cw28-picker-panel{position:absolute;left:12px;right:12px;bottom:calc(var(--ciao-nav-h,72px) + env(safe-area-inset-bottom,0px) + 12px);max-width:360px;margin:auto;padding:12px;border:1px solid rgba(135,155,255,.20);border-radius:20px;background:rgba(7,14,36,.97);box-shadow:0 22px 65px rgba(0,0,0,.48),inset 0 1px 0 rgba(255,255,255,.06);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);pointer-events:auto}
.cw28-picker-title{display:flex;align-items:center;justify-content:space-between;margin:0 2px 10px;color:#fff;font:800 12px/1.2 'Manrope',sans-serif}
.cw28-picker-title small{color:rgba(255,255,255,.45);font-size:10px;font-weight:700}
.cw28-picker-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:7px}
.cw28-picker-grid button{height:43px;border:1px solid rgba(255,255,255,.09);border-radius:13px;background:rgba(255,255,255,.055);color:#fff;font:900 16px/1 'Manrope',sans-serif;touch-action:manipulation}
.cw28-picker-grid button:active{transform:scale(.96);background:rgba(49,80,255,.25);border-color:rgba(116,139,255,.36)}
@media(max-width:390px){
#ciao-miniapp-root .cwpred-card-main{grid-template-columns:minmax(0,1fr) 88px minmax(0,1fr)!important;gap:4px!important}
#ciao-miniapp-root .cw28-score-line{grid-template-columns:36px 8px 36px;gap:2px}
#ciao-miniapp-root .cw28-score-pick{width:36px;height:36px;border-radius:11px;font-size:18px}
.cw28-picker-panel{left:9px;right:9px;padding:10px;border-radius:18px}
.cw28-picker-grid{gap:6px}
.cw28-picker-grid button{height:40px;border-radius:12px;font-size:15px}
}
</style>
<script>
(function(){
  let active=null;
  function esc(v){return typeof __cwPredEsc==='function'?__cwPredEsc(v):String(v??'')}
  function picker(){
    let el=document.getElementById('cw28-score-picker');
    if(el)return el;
    el=document.createElement('div');
    el.id='cw28-score-picker';
    el.className='cw28-picker';
    el.innerHTML='<div class="cw28-picker-backdrop" data-cw28-close></div><div class="cw28-picker-panel" role="dialog" aria-modal="true"><div class="cw28-picker-title"><span>Выберите голы</span><small>0–9</small></div><div class="cw28-picker-grid">'+Array.from({length:10},(_,i)=>'<button type="button" data-cw28-score="'+i+'">'+i+'</button>').join('')+'</div></div>';
    document.body.appendChild(el);
    el.addEventListener('click',e=>{
      if(e.target.closest('[data-cw28-close]')){close();return}
      const b=e.target.closest('[data-cw28-score]');
      if(!b||!active)return;
      apply(Number(b.getAttribute('data-cw28-score')));
      close();
    });
    return el;
  }
  function close(){const el=document.getElementById('cw28-score-picker');if(el)el.classList.remove('open');active=null}
  function open(btn){
    const card=btn.closest('[data-cwpred-match],[data-mid]');
    if(!card)return;
    active={btn,card,side:String(btn.getAttribute('data-cwpred-pick')||'h'),external:card.hasAttribute('data-cwpred-match')};
    picker().classList.add('open');
    try{tg?.HapticFeedback?.selectionChanged?.()}catch(_e){}
  }
  function apply(n){
    if(!active||!Number.isInteger(n)||n<0||n>9)return;
    const side=active.side==='a'?'a':'h';
    if(active.external){
      const key=String(active.card.getAttribute('data-cwpred-match')||'');
      const match=(__cwPredSelectedGroup()?.matches||[]).find(x=>String(x?.matchId||'')===key);
      if(!match?.open)return;
      const cur=__cwPredExternalScoreOf(match),next={h:Number(cur.h)||0,a:Number(cur.a)||0};
      next[side]=n;
      __cwPredExternalDraft.set(key,next);
      active.btn.textContent=String(n);
      __cw26PredSetState('external',key,'dirty');
    }else{
      const id=Number(active.card.getAttribute('data-mid')||0),match=(S?.round?.matches||[]).find(x=>Number(x.id)===id);
      if(!match?.open)return;
      const cur=draft.get(id)||{h:Number(match?.prediction?.home_score??0),a:Number(match?.prediction?.away_score??0)},next={h:Number(cur.h)||0,a:Number(cur.a)||0};
      next[side]=n;
      draft.set(id,next);
      active.btn.textContent=String(n);
      __cw26PredSetState('serie',id,'dirty');
    }
    __cw26PredScheduleAutosave();
    try{tg?.HapticFeedback?.selectionChanged?.()}catch(_e){}
  }
  document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});
  root.addEventListener('click',e=>{const b=e.target.closest('[data-cwpred-pick]');if(!b)return;e.preventDefault();e.stopPropagation();open(b)});

  __cwPredExternalEditCard=function(match){
    const value=__cwPredExternalScoreOf(match),key=String(match?.matchId||''),dirty=__cwPredExternalDraft.has(key),saved=!!match?.prediction;
    const score=match?.open?'<div class="cw28-score-line"><button type="button" class="cw28-score-pick" data-cwpred-pick="h" aria-label="Голы хозяев">'+value.h+'</button><span class="cw28-score-colon">:</span><button type="button" class="cw28-score-pick" data-cwpred-pick="a" aria-label="Голы гостей">'+value.a+'</button></div>':'<div class="cwpred-locked-prediction">'+esc(__cwPredExternalPredictionText(match))+'</div>';
    return '<article class="cwpred-card cwpred-external-card '+(match?.open?'open':'closed')+'" data-cwpred-match="'+esc(key)+'"><div class="cwpred-card-top"><span class="cwpred-status">'+esc(__cwPredStatus(match))+'</span><span class="cwpred-kickoff">'+esc(__cwPredDateTime(match?.kickoffAt))+'</span></div><div class="cwpred-card-main">'+__cwPredExternalTeamHtml(match?.homeTeam,'home')+'<div class="cwpred-score-zone">'+score+'<div class="cwpred-save-state '+(dirty?'dirty':saved?'saved':'')+'">'+(dirty?'Изменено':saved?'✓ Сохранено':match?.open?'Нажмите на счёт':'Прогноз не сделан')+'</div></div>'+__cwPredExternalTeamHtml(match?.awayTeam,'away')+'</div><div class="cwpred-card-bottom"><span>'+esc(__cwPredDeadlineText(match))+'</span>'+(__cwPredRealScore(match)?'<span>'+esc(__cwPredRealScore(match))+'</span>':'')+'</div></article>';
  };
  __cwPredSerieEditCard=function(match){
    const v=scoreOf(match),saved=!!match?.prediction,dirty=draft.has(Number(match.id));
    const score=match.open?'<div class="cw28-score-line"><button type="button" class="cw28-score-pick" data-cwpred-pick="h" aria-label="Голы хозяев">'+v.h+'</button><span class="cw28-score-colon">:</span><button type="button" class="cw28-score-pick" data-cwpred-pick="a" aria-label="Голы гостей">'+v.a+'</button></div>':'<div class="cwpred-locked-prediction">'+(saved?String(match.prediction.home_score)+' : '+String(match.prediction.away_score):'Прогноз не сделан')+'</div>';
    return '<div class="match cwpred-card cwpred-serie-card '+(match.open?'open':'closed')+'" data-mid="'+Number(match.id)+'"><div class="cwpred-card-top"><span class="cwpred-status">'+esc(__cwPredSerieStatus(match))+'</span><span class="cwpred-kickoff">'+esc(typeof fmt==='function'?fmt(match.kickoff_at):'')+'</span></div><div class="cwpred-card-main">'+__cwPredSerieTeamHtml(match.home,'home')+'<div class="cwpred-score-zone">'+score+'<div class="cwpred-save-state '+(dirty?'dirty':saved?'saved':'')+'">'+(dirty?'Изменено':saved?'✓ Сохранено':match.open?'Нажмите на счёт':'Прогноз не сделан')+'</div></div>'+__cwPredSerieTeamHtml(match.away,'away')+'</div><div class="cwpred-card-bottom"><span>'+(match.open?'Дедлайн за 15 минут до начала':'Прогноз закрыт')+'</span>'+(__cwPredSerieRealScore(match)?'<span>'+esc(__cwPredSerieRealScore(match))+'</span>':'')+'</div></div>';
  };
})();
</script>
<!-- /ciao-v28-score-picker-20260908 -->
'''
if '</body>' not in s:
    raise SystemExit('missing body close')
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
