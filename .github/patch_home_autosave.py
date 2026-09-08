#!/usr/bin/env python3
from pathlib import Path
import sys, re

PATH = Path('index.html')
MARKER = '/* ciao-v26-home-entry-autosave-20260908 */'

def die(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(1)

def expect(cond, msg):
    if not cond:
        die(msg)

def replace_exact(s, old, new, count=1):
    n = s.count(old)
    if n < count:
        die(f'missing target ({n}<{count}): {old[:120]!r}')
    return s.replace(old, new, count)

def replace_last_exact(s, old, new):
    i = s.rfind(old)
    if i < 0:
        die(f'missing last target: {old[:120]!r}')
    return s[:i] + new + s[i+len(old):]

def red(s):
    expect(MARKER not in s, 'RED expected feature marker to be absent')
    expect('Date.now()-__cwHomeExternalLoadedAt>=15000' in s, 'RED expected old Home 15s external refresh')
    expect("if(tab!=='predict')return await __cwHomePredLegacyRefreshVisibleNow();" in s, 'RED expected Home periodic refresh wrapper')
    tail_ext = s[s.rfind('__cwPredExternalHtml=function(){'):]
    expect('data-cwpred-action=\\"save\\"' in tail_ext, 'RED expected manual external save button')
    tail_serie = s[s.rfind('__cwPredSerieHtml=function(){'):]
    expect('id=\\"saveAll\\"' in tail_serie, 'RED expected manual Serie A save button')
    print('RED: expected old behavior present')

def green(s):
    expect(MARKER in s, 'GREEN missing feature marker')
    expect('function __cwHomeEnsureExternal(){if(!__cwHomeExternalLoading&&!__cwHomeExternalByCompetition.size)' in s, 'GREEN Home ensure must be one-shot only')
    expect("if(tab==='predict')return false;" in s, 'GREEN Home must not participate in periodic 15s refresh')
    expect('async function __cw26EnterHomeFresh()' in s, 'GREEN missing fresh-on-entry Home flow')
    expect('await __cw26PredAutosaveFlush({force:true})' in s, 'GREEN navigation must flush autosave')
    expect('const __CW26_PRED_AUTOSAVE_DELAY=800;' in s, 'GREEN autosave debounce must be 800ms')
    expect('Не сохранено · повторяем' in s and 'Сохраняем…' in s and '✓ Сохранено' in s, 'GREEN missing autosave states')
    expect("document.addEventListener('visibilitychange',__cw26PredVisibilityFlush)" in s, 'GREEN missing visibility autosave flush')
    ext_start = s.rfind('__cwPredExternalHtml=function(){')
    ext_end = s.find('\n\n  __cwPredSerieHtml=function(){', ext_start)
    ext = s[ext_start:ext_end]
    expect('data-cwpred-action=\\"save\\"' not in ext and 'cwpred-savebar' not in ext, 'GREEN active external renderer still has save button')
    serie_start = s.rfind('__cwPredSerieHtml=function(){')
    serie_end = s.find('\n\n  const __cwPredUxLegacyOpenHub', serie_start)
    serie = s[serie_start:serie_end]
    expect('id=\\"saveAll\\"' not in serie and 'cwpred-savebar' not in serie, 'GREEN active Serie A renderer still has save button')
    expect('async function __cwPredOpenHub(){await __cw26PredAutosaveFlush({force:true});' in s, 'GREEN hub navigation must flush autosave')
    expect("async function __cwPredSetMode(mode){if(__cwPredMode==='edit'&&mode==='mine')await __cw26PredAutosaveFlush({force:true});" in s, 'GREEN mode switch must flush autosave')
    print('GREEN: source contract satisfied')

def patch(s):
    if MARKER in s:
        die('feature marker already present')

    old_ensure = "function __cwHomeEnsureExternal(){if(!__cwHomeExternalLoading&&(!__cwHomeExternalByCompetition.size||Date.now()-__cwHomeExternalLoadedAt>=15000)){Promise.resolve().then(()=>__cwHomeLoadExternal()).catch(()=>{})}}"
    new_ensure = "function __cwHomeEnsureExternal(){if(!__cwHomeExternalLoading&&!__cwHomeExternalByCompetition.size){Promise.resolve().then(()=>__cwHomeLoadExternal()).catch(()=>{});return true}return false}"
    s = replace_exact(s, old_ensure, new_ensure)

    load_token = '  async function __cwHomeLoadExternal(){'
    expect(load_token in s, 'missing Home external loader')
    s = s.replace(load_token, '  let __cw26HomeEntryBusy=false;\n' + load_token, 1)

    old_external_finish = "if(tab==='predict'&&!__cwHomeExternalCenter)try{if(document.getElementById('cw225-start-cover'))render();else{__cw23PolishToday(main);__cw23PolishFavorite(main);__cwHomeBindPolish()}}catch(_e){}"
    new_external_finish = "if(tab==='predict'&&!__cwHomeExternalCenter&&!__cw26HomeEntryBusy)try{if(document.getElementById('cw225-start-cover'))render();else{__cw23PolishToday(main);__cw23PolishFavorite(main);__cwHomeBindPolish()}}catch(_e){}"
    s = replace_exact(s, old_external_finish, new_external_finish)

    helper = r'''
  /* ciao-v26-home-entry-autosave-20260908 */
  async function __cw26EnterHomeFresh(){
    if(__cw26HomeEntryBusy)return false;
    __cw26HomeEntryBusy=true;
    matchViewId=null;matchData=null;root.classList.remove('match-center-open');
    tab='predict';
    const keptDraft=new Map(draft);
    if(main)main.innerHTML=typeof LOADER_HTML==='string'?LOADER_HTML:'<div class="cwpred-state">Обновляем Главную…</div>';
    __cwHomeExternalLoadedAt=0;
    const externalPromise=Promise.resolve().then(()=>__cwHomeLoadExternal()).catch(()=>false);
    try{
      const next=await api({action:'state',round:S?.selected_round});
      S=next;selectedRound=next?.selected_round;
      draft.clear();for(const [k,v] of keptDraft)draft.set(k,v);
      render();
      Promise.resolve(externalPromise).then(()=>{if(tab==='predict'&&!__cwHomeExternalCenter&&!__cw26HomeEntryBusy)try{__cw23PolishToday(main);__cw23PolishFavorite(main);__cwHomeBindPolish()}catch(_e){}}).catch(()=>{});
      return true;
    }catch(error){
      if(main){
        main.innerHTML='<div class="cwpred-state cwpred-state--error"><b>Не удалось обновить Главную</b><button type="button" data-cw26-home-retry>Повторить</button></div>';
        main.querySelector?.('[data-cw26-home-retry]')?.addEventListener('click',()=>__cw26EnterHomeFresh());
      }
      return false;
    }finally{
      __cw26HomeEntryBusy=false;
    }
  }
'''
    anchor = '  function __cwHomeEnsureExternal(){if(!__cwHomeExternalLoading&&!__cwHomeExternalByCompetition.size){Promise.resolve().then(()=>__cwHomeLoadExternal()).catch(()=>{});return true}return false}\n'
    expect(anchor in s, 'missing new Home ensure anchor')
    s = s.replace(anchor, anchor + helper, 1)

    old_refresh = '''  const __cwHomePredLegacyRefreshVisibleNow=__cwRefreshVisibleNow;
  __cwRefreshVisibleNow=async function(){
    if(tab!=='predict')return await __cwHomePredLegacyRefreshVisibleNow();
    if(document.hidden||__cwRefreshBusy)return false;
    __cwRefreshBusy=true;
    const seq=++__cwRefreshSeq;
    const screenKey=__cwRefreshScreenKey();
    try{return await __cwRefreshCurrentCoreScreen(seq,screenKey)}
    finally{__cwRefreshBusy=false}
  };'''
    new_refresh = '''  const __cwHomePredLegacyRefreshVisibleNow=__cwRefreshVisibleNow;
  __cwRefreshVisibleNow=async function(){
    if(tab==='predict')return false;
    return await __cwHomePredLegacyRefreshVisibleNow();
  };'''
    s = replace_last_exact(s, old_refresh, new_refresh)

    old_nav = "root.querySelectorAll('.nav button').forEach(b=>b.onclick=()=>{matchViewId=null;matchData=null;root.classList.remove('match-center-open');tab=b.dataset.tab;render()});"
    new_nav = '''root.querySelectorAll('.nav button').forEach(b=>b.onclick=async()=>{
    const target=String(b.dataset.tab||'');
    if(tab==='mine'&&typeof __cw26PredAutosaveFlush==='function')await __cw26PredAutosaveFlush({force:true});
    matchViewId=null;matchData=null;root.classList.remove('match-center-open');
    if(target==='predict'&&tab!=='predict'&&typeof __cw26EnterHomeFresh==='function'){await __cw26EnterHomeFresh();return}
    tab=target;render()
  });'''
    s = replace_exact(s, old_nav, new_nav)

    old_state_css = '#ciao-miniapp-root .cwpred-save-state.saved{color:#8be3b4}#ciao-miniapp-root .cwpred-save-state.dirty{color:#ffd28a}'
    new_state_css = old_state_css + '#ciao-miniapp-root .cwpred-save-state.saving{color:#aab8ff}#ciao-miniapp-root .cwpred-save-state.error{color:#ff96a5}'
    s = replace_exact(s, old_state_css, new_state_css)

    s = replace_exact(s, "(dirty?'Не сохранено':saved?'Сохранено':'Прогноз не сделан')", "(dirty?'Изменено':saved?'✓ Сохранено':match?.open?'Измените счёт':'Прогноз не сделан')")
    s = replace_exact(s, "(saved?'Сохранено':match.open?'Можно сохранить':'Прогноз не сделан')", "(saved?'✓ Сохранено':match.open?'Измените счёт':'Прогноз не сделан')")

    old_mode = '''  function __cwPredSetMode(mode){
    __cwPredMode=mode==='mine'?'mine':'edit';
    render()
  }'''
    new_mode = '''  async function __cwPredSetMode(mode){if(__cwPredMode==='edit'&&mode==='mine')await __cw26PredAutosaveFlush({force:true});
    __cwPredMode=mode==='mine'?'mine':'edit';
    render()
  }'''
    s = replace_exact(s, old_mode, new_mode)

    old_hub = "function __cwPredOpenHub(){__cwPredRequestVersion+=1;__cwPredCompetition='';__cwPredStageKey='';__cwPredExternalPayload=null;__cwPredExternalDraft.clear();__cwPredLoading=false;__cwPredSaving=false;__cwPredError='';__cwPredRefreshError='';__cwPredApplyTheme();render()}"
    new_hub = "async function __cwPredOpenHub(){await __cw26PredAutosaveFlush({force:true});__cwPredRequestVersion+=1;__cwPredCompetition='';__cwPredStageKey='';__cwPredExternalPayload=null;__cwPredExternalDraft.clear();__cwPredLoading=false;__cwPredSaving=false;__cwPredError='';__cwPredRefreshError='';__cwPredApplyTheme();render()}"
    s = replace_exact(s, old_hub, new_hub)

    old_open_comp = "async function __cwPredOpenCompetition(key){if(!__cwPredMeta(key))return;if(__cwPredCompetition&&__cwPredCompetition!==key)__cwPredExternalDraft.clear();__cwPredRequestVersion+=1;__cwPredCompetition=key;__cwPredStageKey='';__cwPredExternalPayload=null;__cwPredLoading=false;__cwPredSaving=false;__cwPredError='';__cwPredRefreshError='';__cwPredApplyTheme();if(key==='serie_a'){render();return}render();await __cwPredLoadExternal(key,{quiet:false})}"
    new_open_comp = "async function __cwPredOpenCompetition(key){if(!__cwPredMeta(key))return;if(__cwPredCompetition&&__cwPredCompetition!==key){await __cw26PredAutosaveFlush({force:true});__cwPredExternalDraft.clear()}__cwPredRequestVersion+=1;__cwPredCompetition=key;__cwPredStageKey='';__cwPredExternalPayload=null;__cwPredLoading=false;__cwPredSaving=false;__cwPredError='';__cwPredRefreshError='';__cwPredApplyTheme();if(key==='serie_a'){render();return}render();await __cwPredLoadExternal(key,{quiet:false})}"
    s = replace_exact(s, old_open_comp, new_open_comp)

    autosave = r'''
  const __CW26_PRED_AUTOSAVE_DELAY=800;
  let __cw26PredAutosaveTimer=0,__cw26PredAutosaveBusy=false,__cw26PredAutosaveAgain=false;

  function __cw26PredSame(a,b){return !!a&&!!b&&Number(a.h)===Number(b.h)&&Number(a.a)===Number(b.a)}
  function __cw26PredExternalCard(key){return [...(root.querySelectorAll?.('[data-cwpred-match]')||[])].find(el=>String(el.getAttribute?.('data-cwpred-match')||'')===String(key))||null}
  function __cw26PredSerieCard(id){return root.querySelector?.('[data-mid="'+String(Number(id))+'"]')||null}
  function __cw26PredSetState(kind,key,state,customText){
    const card=kind==='external'?__cw26PredExternalCard(key):__cw26PredSerieCard(key),el=card?.querySelector?.('.cwpred-save-state');
    if(!el)return;
    el.classList.remove('dirty','saving','saved','error');
    if(state)el.classList.add(state);
    const copy={dirty:'Изменено',saving:'Сохраняем…',saved:'✓ Сохранено',error:'Не сохранено · повторяем'};
    el.textContent=customText||copy[state]||'';
  }
  function __cw26PatchExternalCard(card,key,next){
    const values=card?.querySelectorAll?.('.cwpred-score-side b')||[];
    if(values[0])values[0].textContent=String(next.h);
    if(values[1])values[1].textContent=String(next.a);
    __cw26PredSetState('external',key,'dirty');
  }
  function __cw26PatchSerieCard(card,id,next){
    const values=card?.querySelectorAll?.('.cwpred-score-side .score-value')||[];
    const h=card?.querySelector?.('[data-score-side="h"]')||values[0],a=card?.querySelector?.('[data-score-side="a"]')||values[1];
    if(h)h.textContent=String(next.h);if(a)a.textContent=String(next.a);
    __cw26PredSetState('serie',id,'dirty');
  }
  function __cw26PredHasPending(){
    if(__cwPredCompetition&&__cwPredIsExternal(__cwPredCompetition))return __cwPredExternalDraft.size>0;
    return draft.size>0;
  }
  function __cw26PredScheduleAutosave(delay=__CW26_PRED_AUTOSAVE_DELAY){
    if(__cw26PredAutosaveTimer)clearTimeout(__cw26PredAutosaveTimer);
    __cw26PredAutosaveTimer=setTimeout(()=>{__cw26PredAutosaveTimer=0;__cw26PredAutosaveFlush().catch(()=>{})},Math.max(0,Number(delay)||0));
  }
  async function __cw26PredAutosaveSerie(){
    const matches=Array.isArray(S?.round?.matches)?S.round.matches:[],byId=new Map(matches.map(m=>[Number(m.id),m])),batch=[];
    for(const [rawId,value] of draft){const id=Number(rawId),m=byId.get(id);if(!m?.open)continue;batch.push({id,value:{h:Number(value.h)||0,a:Number(value.a)||0},match:m})}
    if(!batch.length)return true;
    batch.forEach(x=>__cw26PredSetState('serie',x.id,'saving'));
    try{
      await api({action:'save_predictions',round:S.selected_round,predictions:batch.map(x=>({match_id:x.id,home_score:x.value.h,away_score:x.value.a}))});
      for(const x of batch){
        x.match.prediction={...(x.match.prediction||{}),home_score:x.value.h,away_score:x.value.a};
        const current=draft.get(x.id);
        if(__cw26PredSame(current,x.value))draft.delete(x.id);
        __cw26PredSetState('serie',x.id,draft.has(x.id)?'dirty':'saved');
      }
      return true;
    }catch(_e){
      batch.forEach(x=>__cw26PredSetState('serie',x.id,'error'));
      return false;
    }
  }
  async function __cw26PredAutosaveExternal(){
    const group=__cwPredSelectedGroup();if(!group||!__cwPredCompetition)return true;
    const batch=[];
    for(const match of group.matches||[]){const key=String(match?.matchId||'');if(!match?.open||!__cwPredExternalDraft.has(key))continue;const value=__cwPredExternalDraft.get(key);batch.push({key,value:{h:Number(value.h)||0,a:Number(value.a)||0},match})}
    if(!batch.length)return true;
    batch.forEach(x=>__cw26PredSetState('external',x.key,'saving'));
    try{
      const response=await fetch(__CWPRED_EXTERNAL_API,{method:'POST',headers:{'content-type':'application/json','x-telegram-init-data':String(initData||'')},body:JSON.stringify({action:'save_predictions',competition:__cwPredCompetition,predictions:batch.map(x=>({match_id:x.key,home_score:x.value.h,away_score:x.value.a}))}),cache:'no-store'});
      const body=await response.json().catch(()=>({}));if(!response.ok||!body?.ok)throw new Error(String(body?.error||('HTTP '+response.status)));
      const closed=new Set((body?.data?.closed||[]).map(String)),invalid=new Set((body?.data?.invalid||[]).map(String));
      for(const x of batch){
        if(closed.has(x.key)||invalid.has(x.key)){__cwPredExternalDraft.delete(x.key);__cw26PredSetState('external',x.key,'error','Не удалось сохранить');continue}
        x.match.prediction={...(x.match.prediction||{}),home_score:x.value.h,away_score:x.value.a};
        const current=__cwPredExternalDraft.get(x.key);
        if(__cw26PredSame(current,x.value))__cwPredExternalDraft.delete(x.key);
        __cw26PredSetState('external',x.key,__cwPredExternalDraft.has(x.key)?'dirty':'saved');
      }
      return true;
    }catch(_e){
      batch.forEach(x=>__cw26PredSetState('external',x.key,'error'));
      return false;
    }
  }
  async function __cw26PredAutosaveFlush({force=false}={}){
    if(__cw26PredAutosaveTimer){clearTimeout(__cw26PredAutosaveTimer);__cw26PredAutosaveTimer=0}
    if(__cw26PredAutosaveBusy){__cw26PredAutosaveAgain=true;return false}
    if(!force&&!__cw26PredHasPending())return true;
    __cw26PredAutosaveBusy=true;
    let ok=false;
    try{
      ok=__cwPredCompetition&&__cwPredIsExternal(__cwPredCompetition)?await __cw26PredAutosaveExternal():await __cw26PredAutosaveSerie();
      return ok;
    }finally{
      __cw26PredAutosaveBusy=false;
      if(__cw26PredAutosaveAgain||(__cw26PredHasPending()&&ok)){__cw26PredAutosaveAgain=false;__cw26PredScheduleAutosave(350)}
    }
  }
  function __cw26PredVisibilityFlush(){
    if(document.hidden){__cw26PredAutosaveFlush({force:true}).catch(()=>{})}
    else if(__cw26PredHasPending())__cw26PredScheduleAutosave(0);
  }
  document.addEventListener('visibilitychange',__cw26PredVisibilityFlush);
  window.addEventListener?.('pagehide',()=>{__cw26PredAutosaveFlush({force:true}).catch(()=>{})});
'''
    insert_at = s.rfind('  __cwPredExternalHtml=function(){')
    expect(insert_at >= 0, 'missing active external renderer for autosave insertion')
    s = s[:insert_at] + autosave + '\n' + s[insert_at:]

    ext_start = s.rfind('  __cwPredExternalHtml=function(){')
    ext_end = s.find('\n\n  __cwPredSerieHtml=function(){', ext_start)
    expect(ext_start >= 0 and ext_end > ext_start, 'cannot isolate active external renderer')
    ext_old = s[ext_start:ext_end]
    ext_new = re.sub(r"const save=!locked&&__cwPredExternalCanSave\(group\)\?'<div class=\\\"cwpred-savebar\\\">.*?</button></div>':'';", '', ext_old)
    ext_new = ext_new.replace('+save};', '};')
    expect('data-cwpred-action=\\"save\\"' not in ext_new and 'cwpred-savebar' not in ext_new, 'failed to remove active external save control')
    s = s[:ext_start] + ext_new + s[ext_end:]

    serie_start = s.rfind('  __cwPredSerieHtml=function(){')
    serie_end = s.find('\n\n  const __cwPredUxLegacyOpenHub', serie_start)
    expect(serie_start >= 0 and serie_end > serie_start, 'cannot isolate active Serie A renderer')
    serie_old = s[serie_start:serie_end]
    serie_new = re.sub(r"const save=__cwPredMode==='edit'&&S\.round\.matches\.some\(match=>match\.open\)\?'<div class=\\\"savebar cwpred-savebar\\\">.*?</button></div>':'';", '', serie_old)
    serie_new = serie_new.replace('+save};', '};')
    expect('id=\\"saveAll\\"' not in serie_new and 'cwpred-savebar' not in serie_new, 'failed to remove active Serie A save control')
    s = s[:serie_start] + serie_new + s[serie_end:]

    s = replace_exact(s, '__cwPredExternalDraft.set(key,next);render()', '__cwPredExternalDraft.set(key,next);__cw26PatchExternalCard(host,key,next);__cw26PredScheduleAutosave()')

    old_serie_tail = 'if(status)status.innerHTML=predictionStatusHtml(m);try{tg.HapticFeedback.selectionChanged()}catch(_e){}});'
    new_serie_tail = 'if(status)status.innerHTML=predictionStatusHtml(m);__cw26PatchSerieCard(box,id,nv);__cw26PredScheduleAutosave();try{tg.HapticFeedback.selectionChanged()}catch(_e){}});'
    s = replace_exact(s, old_serie_tail, new_serie_tail)

    old_stage = "root.querySelectorAll('[data-cwpred-stage]').forEach(btn=>btn.addEventListener('click',()=>{__cwPredStageKey=String(btn.getAttribute('data-cwpred-stage')||'');render()}));"
    new_stage = "root.querySelectorAll('[data-cwpred-stage]').forEach(btn=>btn.addEventListener('click',async()=>{await __cw26PredAutosaveFlush({force:true});__cwPredStageKey=String(btn.getAttribute('data-cwpred-stage')||'');render()}));"
    s = replace_exact(s, old_stage, new_stage)

    return s

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    s = PATH.read_text(encoding='utf-8')
    if mode == '--red':
        red(s); return
    if mode == '--green':
        green(s); return
    if mode == '--patch':
        PATH.write_text(patch(s), encoding='utf-8')
        print('patched')
        return
    die('usage: --red | --patch | --green')

if __name__ == '__main__':
    main()
