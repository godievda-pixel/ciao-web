#!/usr/bin/env python3
from pathlib import Path
import sys
P=Path('index.html')
M='/* ciao-v26-home-entry-autosave-20260908 */'

def fail(x): print(x,file=sys.stderr); raise SystemExit(1)
def need(c,x):
    if not c: fail(x)
def once(s,a,b):
    need(a in s,'missing: '+a[:100]); return s.replace(a,b,1)
def last(s,a,b):
    i=s.rfind(a); need(i>=0,'missing last: '+a[:100]); return s[:i]+b+s[i+len(a):]

def check(s):
    need(M in s,'missing marker')
    need("if(tab==='predict')return false;" in s,'Home still refreshes on timer')
    need('async function __cw26EnterHomeFresh()' in s,'missing fresh Home entry')
    need('const __CW26_PRED_AUTOSAVE_DELAY=800;' in s,'missing autosave debounce')
    need('Не сохранено · повторяем' in s and 'Сохраняем…' in s and '✓ Сохранено' in s,'missing autosave states')
    a=s.rfind('__cwPredExternalHtml=function(){'); b=s.find('\n\n  __cwPredSerieHtml=function(){',a); ext=s[a:b]
    need('data-cwpred-action="save"' not in ext and 'cwpred-savebar' not in ext,'external manual save remains')
    a=s.rfind('__cwPredSerieHtml=function(){'); b=s.find('\n\n  const __cwPredUxLegacyOpenHub',a); ser=s[a:b]
    need('id="saveAll"' not in ser and 'cwpred-savebar' not in ser,'Serie manual save remains')
    need("document.addEventListener('visibilitychange',__cw26PredVisibilityFlush)" in s,'missing visibility flush')
    print('CONTRACT PASS')

def apply(s):
    need(M not in s,'already applied')
    s=once(s,
      "function __cwHomeEnsureExternal(){if(!__cwHomeExternalLoading&&(!__cwHomeExternalByCompetition.size||Date.now()-__cwHomeExternalLoadedAt>=15000)){Promise.resolve().then(()=>__cwHomeLoadExternal()).catch(()=>{})}}",
      "function __cwHomeEnsureExternal(){if(!__cwHomeExternalLoading&&!__cwHomeExternalByCompetition.size){Promise.resolve().then(()=>__cwHomeLoadExternal()).catch(()=>{});return true}return false}")
    s=once(s,"  async function __cwHomeLoadExternal(){","  let __cw26HomeEntryBusy=false;\n  async function __cwHomeLoadExternal(){")
    s=once(s,
      "if(tab==='predict'&&!__cwHomeExternalCenter)try{if(document.getElementById('cw225-start-cover'))render();else{__cw23PolishToday(main);__cw23PolishFavorite(main);__cwHomeBindPolish()}}catch(_e){}",
      "if(tab==='predict'&&!__cwHomeExternalCenter&&!__cw26HomeEntryBusy)try{if(document.getElementById('cw225-start-cover'))render();else{__cw23PolishToday(main);__cw23PolishFavorite(main);__cwHomeBindPolish()}}catch(_e){}")
    anchor="  function __cwHomeEnsureExternal(){if(!__cwHomeExternalLoading&&!__cwHomeExternalByCompetition.size){Promise.resolve().then(()=>__cwHomeLoadExternal()).catch(()=>{});return true}return false}\n"
    helper=r'''  /* ciao-v26-home-entry-autosave-20260908 */
  async function __cw26EnterHomeFresh(){
    if(__cw26HomeEntryBusy)return false;__cw26HomeEntryBusy=true;
    matchViewId=null;matchData=null;root.classList.remove('match-center-open');tab='predict';
    const keptDraft=new Map(draft);
    if(main)main.innerHTML=typeof LOADER_HTML==='string'?LOADER_HTML:'<div class="cwpred-state">Обновляем Главную…</div>';
    __cwHomeExternalLoadedAt=0;
    const ext=Promise.resolve().then(()=>__cwHomeLoadExternal()).catch(()=>false);
    try{
      const next=await api({action:'state',round:S?.selected_round});S=next;selectedRound=next?.selected_round;
      draft.clear();for(const [k,v] of keptDraft)draft.set(k,v);render();
      Promise.resolve(ext).then(()=>{if(tab==='predict'&&!__cwHomeExternalCenter)try{__cw23PolishToday(main);__cw23PolishFavorite(main);__cwHomeBindPolish()}catch(_e){}}).catch(()=>{});
      return true;
    }catch(_e){
      if(main){main.innerHTML='<div class="cwpred-state cwpred-state--error"><b>Не удалось обновить Главную</b><button type="button" data-cw26-home-retry>Повторить</button></div>';main.querySelector?.('[data-cw26-home-retry]')?.addEventListener('click',()=>__cw26EnterHomeFresh())}
      return false;
    }finally{__cw26HomeEntryBusy=false}
  }
'''
    need(anchor in s,'Home anchor missing'); s=s.replace(anchor,anchor+helper,1)
    old='''  const __cwHomePredLegacyRefreshVisibleNow=__cwRefreshVisibleNow;
  __cwRefreshVisibleNow=async function(){
    if(tab!=='predict')return await __cwHomePredLegacyRefreshVisibleNow();
    if(document.hidden||__cwRefreshBusy)return false;
    __cwRefreshBusy=true;
    const seq=++__cwRefreshSeq;
    const screenKey=__cwRefreshScreenKey();
    try{return await __cwRefreshCurrentCoreScreen(seq,screenKey)}
    finally{__cwRefreshBusy=false}
  };'''
    new='''  const __cwHomePredLegacyRefreshVisibleNow=__cwRefreshVisibleNow;
  __cwRefreshVisibleNow=async function(){
    if(tab==='predict')return false;
    return await __cwHomePredLegacyRefreshVisibleNow();
  };'''
    s=last(s,old,new)
    s=once(s,"root.querySelectorAll('.nav button').forEach(b=>b.onclick=()=>{matchViewId=null;matchData=null;root.classList.remove('match-center-open');tab=b.dataset.tab;render()});",'''root.querySelectorAll('.nav button').forEach(b=>b.onclick=async()=>{
    const target=String(b.dataset.tab||'');
    if(tab==='mine'&&typeof __cw26PredAutosaveFlush==='function')await __cw26PredAutosaveFlush({force:true});
    matchViewId=null;matchData=null;root.classList.remove('match-center-open');
    if(target==='predict'&&tab!=='predict'&&typeof __cw26EnterHomeFresh==='function'){await __cw26EnterHomeFresh();return}
    tab=target;render()
  });''')
    css='#ciao-miniapp-root .cwpred-save-state.saved{color:#8be3b4}#ciao-miniapp-root .cwpred-save-state.dirty{color:#ffd28a}'
    s=once(s,css,css+'#ciao-miniapp-root .cwpred-save-state.saving{color:#aab8ff}#ciao-miniapp-root .cwpred-save-state.error{color:#ff96a5}')
    s=once(s,"(dirty?'Не сохранено':saved?'Сохранено':'Прогноз не сделан')","(dirty?'Изменено':saved?'✓ Сохранено':match?.open?'Измените счёт':'Прогноз не сделан')")
    s=once(s,"(saved?'Сохранено':match.open?'Можно сохранить':'Прогноз не сделан')","(saved?'✓ Сохранено':match.open?'Измените счёт':'Прогноз не сделан')")
    s=once(s,"  function __cwPredSetMode(mode){\n    __cwPredMode=mode==='mine'?'mine':'edit';\n    render()\n  }","  async function __cwPredSetMode(mode){if(__cwPredMode==='edit'&&mode==='mine')await __cw26PredAutosaveFlush({force:true});\n    __cwPredMode=mode==='mine'?'mine':'edit';\n    render()\n  }")
    s=once(s,"function __cwPredOpenHub(){__cwPredRequestVersion+=1;__cwPredCompetition='';__cwPredStageKey='';__cwPredExternalPayload=null;__cwPredExternalDraft.clear();__cwPredLoading=false;__cwPredSaving=false;__cwPredError='';__cwPredRefreshError='';__cwPredApplyTheme();render()}","async function __cwPredOpenHub(){await __cw26PredAutosaveFlush({force:true});__cwPredRequestVersion+=1;__cwPredCompetition='';__cwPredStageKey='';__cwPredExternalPayload=null;__cwPredExternalDraft.clear();__cwPredLoading=false;__cwPredSaving=false;__cwPredError='';__cwPredRefreshError='';__cwPredApplyTheme();render()}")
    s=once(s,"async function __cwPredOpenCompetition(key){if(!__cwPredMeta(key))return;if(__cwPredCompetition&&__cwPredCompetition!==key)__cwPredExternalDraft.clear();__cwPredRequestVersion+=1;__cwPredCompetition=key;__cwPredStageKey='';__cwPredExternalPayload=null;__cwPredLoading=false;__cwPredSaving=false;__cwPredError='';__cwPredRefreshError='';__cwPredApplyTheme();if(key==='serie_a'){render();return}render();await __cwPredLoadExternal(key,{quiet:false})}","async function __cwPredOpenCompetition(key){if(!__cwPredMeta(key))return;if(__cwPredCompetition&&__cwPredCompetition!==key){await __cw26PredAutosaveFlush({force:true});__cwPredExternalDraft.clear()}__cwPredRequestVersion+=1;__cwPredCompetition=key;__cwPredStageKey='';__cwPredExternalPayload=null;__cwPredLoading=false;__cwPredSaving=false;__cwPredError='';__cwPredRefreshError='';__cwPredApplyTheme();if(key==='serie_a'){render();return}render();await __cwPredLoadExternal(key,{quiet:false})}")
    engine=r'''
  const __CW26_PRED_AUTOSAVE_DELAY=800;
  let __cw26PredAutosaveTimer=0,__cw26PredAutosaveBusy=false,__cw26PredAutosaveAgain=false;
  function __cw26PredSame(a,b){return !!a&&!!b&&Number(a.h)===Number(b.h)&&Number(a.a)===Number(b.a)}
  function __cw26PredExternalCard(k){return [...(root.querySelectorAll?.('[data-cwpred-match]')||[])].find(e=>String(e.getAttribute?.('data-cwpred-match')||'')===String(k))||null}
  function __cw26PredSerieCard(id){return root.querySelector?.('[data-mid="'+String(Number(id))+'"]')||null}
  function __cw26PredSetState(kind,key,state,text){const card=kind==='external'?__cw26PredExternalCard(key):__cw26PredSerieCard(key),el=card?.querySelector?.('.cwpred-save-state');if(!el)return;el.classList.remove('dirty','saving','saved','error');if(state)el.classList.add(state);el.textContent=text||({dirty:'Изменено',saving:'Сохраняем…',saved:'✓ Сохранено',error:'Не сохранено · повторяем'})[state]||''}
  function __cw26PatchExternalCard(card,key,v){const x=card?.querySelectorAll?.('.cwpred-score-side b')||[];if(x[0])x[0].textContent=String(v.h);if(x[1])x[1].textContent=String(v.a);__cw26PredSetState('external',key,'dirty')}
  function __cw26PatchSerieCard(card,id,v){const x=card?.querySelectorAll?.('.cwpred-score-side .score-value')||[],h=card?.querySelector?.('[data-score-side="h"]')||x[0],a=card?.querySelector?.('[data-score-side="a"]')||x[1];if(h)h.textContent=String(v.h);if(a)a.textContent=String(v.a);__cw26PredSetState('serie',id,'dirty')}
  function __cw26PredHasPending(){return __cwPredCompetition&&__cwPredIsExternal(__cwPredCompetition)?__cwPredExternalDraft.size>0:draft.size>0}
  function __cw26PredScheduleAutosave(delay=__CW26_PRED_AUTOSAVE_DELAY){if(__cw26PredAutosaveTimer)clearTimeout(__cw26PredAutosaveTimer);__cw26PredAutosaveTimer=setTimeout(()=>{__cw26PredAutosaveTimer=0;__cw26PredAutosaveFlush().catch(()=>{})},Math.max(0,Number(delay)||0))}
  async function __cw26PredAutosaveSerie(){const ms=Array.isArray(S?.round?.matches)?S.round.matches:[],map=new Map(ms.map(m=>[Number(m.id),m])),b=[];for(const [id0,v] of draft){const id=Number(id0),m=map.get(id);if(m?.open)b.push({id,v:{h:Number(v.h)||0,a:Number(v.a)||0},m})}if(!b.length)return true;b.forEach(x=>__cw26PredSetState('serie',x.id,'saving'));try{await api({action:'save_predictions',round:S.selected_round,predictions:b.map(x=>({match_id:x.id,home_score:x.v.h,away_score:x.v.a}))});for(const x of b){x.m.prediction={...(x.m.prediction||{}),home_score:x.v.h,away_score:x.v.a};const cur=draft.get(x.id);if(__cw26PredSame(cur,x.v))draft.delete(x.id);__cw26PredSetState('serie',x.id,draft.has(x.id)?'dirty':'saved')}return true}catch(_e){b.forEach(x=>__cw26PredSetState('serie',x.id,'error'));return false}}
  async function __cw26PredAutosaveExternal(){const g=__cwPredSelectedGroup();if(!g||!__cwPredCompetition)return true;const b=[];for(const m of g.matches||[]){const k=String(m?.matchId||'');if(m?.open&&__cwPredExternalDraft.has(k)){const v=__cwPredExternalDraft.get(k);b.push({k,v:{h:Number(v.h)||0,a:Number(v.a)||0},m})}}if(!b.length)return true;b.forEach(x=>__cw26PredSetState('external',x.k,'saving'));try{const r=await fetch(__CWPRED_EXTERNAL_API,{method:'POST',headers:{'content-type':'application/json','x-telegram-init-data':String(initData||'')},body:JSON.stringify({action:'save_predictions',competition:__cwPredCompetition,predictions:b.map(x=>({match_id:x.k,home_score:x.v.h,away_score:x.v.a}))}),cache:'no-store'}),j=await r.json().catch(()=>({}));if(!r.ok||!j?.ok)throw new Error(String(j?.error||('HTTP '+r.status)));const closed=new Set((j?.data?.closed||[]).map(String)),invalid=new Set((j?.data?.invalid||[]).map(String));for(const x of b){if(closed.has(x.k)||invalid.has(x.k)){__cwPredExternalDraft.delete(x.k);__cw26PredSetState('external',x.k,'error','Не удалось сохранить');continue}x.m.prediction={...(x.m.prediction||{}),home_score:x.v.h,away_score:x.v.a};const cur=__cwPredExternalDraft.get(x.k);if(__cw26PredSame(cur,x.v))__cwPredExternalDraft.delete(x.k);__cw26PredSetState('external',x.k,__cwPredExternalDraft.has(x.k)?'dirty':'saved')}return true}catch(_e){b.forEach(x=>__cw26PredSetState('external',x.k,'error'));return false}}
  async function __cw26PredAutosaveFlush({force=false}={}){if(__cw26PredAutosaveTimer){clearTimeout(__cw26PredAutosaveTimer);__cw26PredAutosaveTimer=0}if(__cw26PredAutosaveBusy){__cw26PredAutosaveAgain=true;return false}if(!force&&!__cw26PredHasPending())return true;__cw26PredAutosaveBusy=true;let ok=false;try{ok=__cwPredCompetition&&__cwPredIsExternal(__cwPredCompetition)?await __cw26PredAutosaveExternal():await __cw26PredAutosaveSerie();return ok}finally{__cw26PredAutosaveBusy=false;if(__cw26PredAutosaveAgain||(__cw26PredHasPending()&&ok)){__cw26PredAutosaveAgain=false;__cw26PredScheduleAutosave(350)}}}
  function __cw26PredVisibilityFlush(){if(document.hidden)__cw26PredAutosaveFlush({force:true}).catch(()=>{});else if(__cw26PredHasPending())__cw26PredScheduleAutosave(0)}
  document.addEventListener('visibilitychange',__cw26PredVisibilityFlush);
  window.addEventListener?.('pagehide',()=>{__cw26PredAutosaveFlush({force:true}).catch(()=>{})});
'''
    pos=s.rfind('  __cwPredExternalHtml=function(){'); need(pos>=0,'external renderer missing'); s=s[:pos]+engine+'\n'+s[pos:]
    a=s.rfind('  __cwPredExternalHtml=function(){'); b=s.find('\n\n  __cwPredSerieHtml=function(){',a); need(b>a,'external block end missing'); block=s[a:b]; p=block.find('const save='); q=block.find('const lockNote=',p); need(p>=0 and q>p,'external save segment missing'); block=block[:p]+block[q:]; block=block.replace("+'</div>'+save};","+'</div>'};"); s=s[:a]+block+s[b:]
    a=s.rfind('  __cwPredSerieHtml=function(){'); b=s.find('\n\n  const __cwPredUxLegacyOpenHub',a); need(b>a,'Serie block end missing'); block=s[a:b]; p=block.find('const save='); q=block.find('return cover',p); need(p>=0 and q>p,'Serie save segment missing'); block=block[:p]+block[q:]; block=block.replace("+'</div>'+save};","+'</div>'};"); s=s[:a]+block+s[b:]
    s=once(s,'__cwPredExternalDraft.set(key,next);render()','__cwPredExternalDraft.set(key,next);__cw26PatchExternalCard(host,key,next);__cw26PredScheduleAutosave()')
    s=once(s,'if(status)status.innerHTML=predictionStatusHtml(m);try{tg.HapticFeedback.selectionChanged()}catch(_e){}});','if(status)status.innerHTML=predictionStatusHtml(m);__cw26PatchSerieCard(box,id,nv);__cw26PredScheduleAutosave();try{tg.HapticFeedback.selectionChanged()}catch(_e){}});')
    s=once(s,"root.querySelectorAll('[data-cwpred-stage]').forEach(btn=>btn.addEventListener('click',()=>{__cwPredStageKey=String(btn.getAttribute('data-cwpred-stage')||'');render()}));","root.querySelectorAll('[data-cwpred-stage]').forEach(btn=>btn.addEventListener('click',async()=>{await __cw26PredAutosaveFlush({force:true});__cwPredStageKey=String(btn.getAttribute('data-cwpred-stage')||'');render()}));")
    return s

def main():
    s=P.read_text(encoding='utf-8'); mode=sys.argv[1] if len(sys.argv)>1 else 'check'
    if mode=='check': check(s)
    elif mode=='apply': P.write_text(apply(s),encoding='utf-8'); print('PATCH APPLIED')
    else: fail('usage: check|apply')
if __name__=='__main__': main()
