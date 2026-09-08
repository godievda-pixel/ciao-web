from pathlib import Path

p = Path('index.html')
s = p.read_text()


def replace_once(old: str, new: str, label: str):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected 1 exact match, got {n}')
    s = s.replace(old, new, 1)


replace_once(
    "let matchViewId=null, matchData=null, matchReturnTab='calendar', matchLoading=false, matchCenterTab='overview';",
    "let matchViewId=null, matchViewSource='serie_a', matchData=null, matchReturnTab='calendar', matchLoading=false, matchCenterTab='overview';",
    'match state',
)

replace_once(
    "const __cw9FastMatchApi=(id,sections=[])=>__cw9Post(__CW9_MATCH_API,{match_id:Number(id),sections,include_split:false},'Не удалось загрузить Матч-центр');",
    "const __cw9FastMatchApi=(id,sections=[],source=matchViewSource)=>__cw9Post(__CW9_MATCH_API,{source,match_id:Number(id),sections,include_split:false},'Не удалось загрузить Матч-центр');",
    'lazy API helper',
)
replace_once(
    "const __cw9SummaryApi=id=>__cw9Post(__CW9_SUMMARY_API,{match_id:Number(id)},'Не удалось загрузить матч');",
    "const __cw9SummaryApi=(id,source=matchViewSource)=>__cw9Post(__CW9_SUMMARY_API,{source,match_id:Number(id)},'Не удалось загрузить матч');",
    'summary API helper',
)
replace_once(
    "__cw2153PostBase(__CW9_MATCH_API,{match_id:mid,sections:['incidents','player_stats','lineups'],include_split:false},'Не удалось загрузить данные матча')",
    "__cw2153PostBase(__CW9_MATCH_API,{source:String(body?.source||matchViewSource||'serie_a'),match_id:mid,sections:['incidents','player_stats','lineups'],include_split:false},'Не удалось загрузить данные матча')",
    'summary enrichment source',
)

replace_once(
    "JSON.stringify({tab,matchViewId:matchViewId||null,matchCenterTab:matchCenterTab||'overview',clubViewId:clubViewId||null,clubViewTab:typeof clubViewTab==='string'?clubViewTab:'overview',scrollTop:main?.scrollTop||0,ts:Date.now()})",
    "JSON.stringify({tab,matchViewId:matchViewId||null,matchViewSource:String(matchViewSource||'serie_a'),matchCenterTab:matchCenterTab||'overview',clubViewId:clubViewId||null,clubViewTab:typeof clubViewTab==='string'?clubViewTab:'overview',scrollTop:main?.scrollTop||0,ts:Date.now()})",
    'v18 persist source',
)
replace_once(
    "await openMatchCenter(Number(v.matchViewId))",
    "await openMatchCenter(Number(v.matchViewId),String(v.matchViewSource||'serie_a'))",
    'v18 restore source',
)
replace_once(
    "return {ts:Date.now(),tab:String(tab||'predict'),matchId:Number(matchViewId)||0,clubId:Number(clubViewId)||0,matchTab:String(typeof matchCenterTab!=='undefined'?matchCenterTab||'':''),scroll:Number(main?.scrollTop)||0}",
    "return {ts:Date.now(),tab:String(tab||'predict'),matchId:Number(matchViewId)||0,matchSource:String(matchViewSource||'serie_a'),clubId:Number(clubViewId)||0,matchTab:String(typeof matchCenterTab!=='undefined'?matchCenterTab||'':''),scroll:Number(main?.scrollTop)||0}",
    'v22 view source',
)
replace_once(
    "await openMatchCenter(Number(s.matchId))",
    "await openMatchCenter(Number(s.matchId),String(s.matchSource||'serie_a'))",
    'v22 restore source',
)

replace_once(
    "clubReturnSnapshot={tab,matchViewId,matchCenterTab,scrollTop:main?.scrollTop??0}",
    "clubReturnSnapshot={tab,matchViewId,matchViewSource:String(matchViewSource||'serie_a'),matchCenterTab,scrollTop:main?.scrollTop??0}",
    'club return source snapshot',
)
replace_once(
    "if(snap?.matchViewId){matchViewId=snap.matchViewId;matchCenterTab=snap.matchCenterTab||'overview';root.classList.add('match-center-open')}",
    "if(snap?.matchViewId){matchViewId=snap.matchViewId;matchViewSource=String(snap.matchViewSource||'serie_a');matchCenterTab=snap.matchCenterTab||'overview';root.classList.add('match-center-open')}",
    'club return source restore',
)

replace_once(
    "function __cw18MatchContext(d){const m=d?.match||{},",
    "function __cw18MatchContext(d){if(String(d?.source||d?.match?.source||'serie_a')!=='serie_a')return '';const m=d?.match||{},",
    'Serie A context source guard',
)
replace_once(
    "if(matchViewId&&matchData?.match){__cw18PrefetchClub(matchData.match.home?.id);__cw18PrefetchClub(matchData.match.away?.id)}",
    "if(matchViewId&&matchData?.match&&String(matchData?.source||matchData?.match?.source||'serie_a')==='serie_a'){__cw18PrefetchClub(matchData.match.home?.id);__cw18PrefetchClub(matchData.match.away?.id)}",
    'external context prefetch guard',
)

css = '''
<style id="ciao-v32-external-match-center-style">
#ciao-miniapp-root .mc-shell[data-mc-source="external"] .mc-external-crest{object-fit:contain!important;background:transparent!important}
#ciao-miniapp-root .mc-shell[data-mc-source="external"] .mc-external-meta{display:flex;flex-direction:column;align-items:center;gap:4px;margin-top:14px!important;line-height:1.2}
#ciao-miniapp-root .mc-shell[data-mc-source="external"] .mc-external-meta b{font-size:11px;color:#f7f9ff;letter-spacing:-.01em}
#ciao-miniapp-root .mc-shell[data-mc-source="external"] .mc-external-meta span{font-size:9px;color:#9aa8c8}
#ciao-miniapp-root .mc-shell[data-mc-source="external"] .mc-hero,#ciao-miniapp-root .mc-shell[data-mc-source="external"] .mc-section{transition:border-color .18s ease,box-shadow .18s ease,background .18s ease}
#ciao-miniapp-root .mc-shell.mc-theme-ucl .mc-hero{background:radial-gradient(circle at 82% 0%,rgba(126,76,255,.34),transparent 42%),radial-gradient(circle at 8% 18%,rgba(32,88,255,.28),transparent 36%),linear-gradient(145deg,#090c2d,#070b20 68%,#0d1238)!important;border-color:rgba(115,104,255,.30)!important;box-shadow:0 22px 70px rgba(31,23,120,.34),inset 0 1px 0 rgba(255,255,255,.05)!important}
#ciao-miniapp-root .mc-shell.mc-theme-ucl .mc-tab.active{background:linear-gradient(180deg,#654cff,#253cdb)!important;border-color:rgba(146,128,255,.46)!important;box-shadow:0 8px 22px rgba(70,55,220,.30)!important}
#ciao-miniapp-root .mc-shell.mc-theme-ucl .mc-section{border-color:rgba(105,104,255,.17)!important}
#ciao-miniapp-root .mc-shell.mc-theme-uel .mc-hero{background:radial-gradient(circle at 88% 4%,rgba(255,124,28,.32),transparent 40%),linear-gradient(145deg,#171717,#0c0d10 68%,#21150d)!important;border-color:rgba(255,132,42,.30)!important;box-shadow:0 22px 70px rgba(104,48,8,.28),inset 0 1px 0 rgba(255,255,255,.045)!important}
#ciao-miniapp-root .mc-shell.mc-theme-uel .mc-tab.active{background:linear-gradient(180deg,#ff8a2c,#c94b00)!important;border-color:rgba(255,153,76,.48)!important;box-shadow:0 8px 22px rgba(224,93,11,.26)!important}
#ciao-miniapp-root .mc-shell.mc-theme-uel .mc-section{border-color:rgba(255,131,45,.16)!important}
#ciao-miniapp-root .mc-shell.mc-theme-uecl .mc-hero{background:radial-gradient(circle at 84% 2%,rgba(41,220,122,.29),transparent 40%),linear-gradient(145deg,#111a16,#090e0c 68%,#102419)!important;border-color:rgba(55,220,128,.28)!important;box-shadow:0 22px 70px rgba(8,90,47,.27),inset 0 1px 0 rgba(255,255,255,.04)!important}
#ciao-miniapp-root .mc-shell.mc-theme-uecl .mc-tab.active{background:linear-gradient(180deg,#29d77d,#0a934b)!important;border-color:rgba(77,232,149,.44)!important;box-shadow:0 8px 22px rgba(19,151,79,.25)!important}
#ciao-miniapp-root .mc-shell.mc-theme-uecl .mc-section{border-color:rgba(54,213,124,.15)!important}
#ciao-miniapp-root .mc-shell.mc-theme-coppa .mc-hero{background:radial-gradient(circle at 100% 0%,rgba(214,37,54,.23),transparent 34%),radial-gradient(circle at 0% 8%,rgba(32,177,92,.20),transparent 34%),linear-gradient(145deg,#071a3a,#061128 68%,#0a2149)!important;border-color:rgba(83,127,210,.28)!important;box-shadow:0 22px 70px rgba(5,33,85,.32),inset 0 1px 0 rgba(255,255,255,.045)!important}
#ciao-miniapp-root .mc-shell.mc-theme-coppa .mc-tab.active{background:linear-gradient(100deg,#148f55 0%,#1c54ad 51%,#b72b3b 100%)!important;border-color:rgba(123,156,222,.42)!important;box-shadow:0 8px 22px rgba(20,62,130,.27)!important}
#ciao-miniapp-root .mc-shell.mc-theme-coppa .mc-section{border-color:rgba(79,126,204,.16)!important}
#ciao-miniapp-root .cwmt-match-card[data-match-source="external"],#ciao-miniapp-root .cwpred-external-card[data-match-source="external"]{cursor:pointer}
</style>
'''

if 'id="ciao-v32-external-match-center-style"' in s:
    raise SystemExit('v32 style already present')
if s.count('</head>') != 1:
    raise SystemExit(f'head close count {s.count("</head>")}')
s = s.replace('</head>', css + '\n</head>', 1)

block = r'''
  /* ciao-v32-external-match-center-20260908 */
  const __cw32CompetitionLabels={ucl:'Лига чемпионов',uel:'Лига Европы',uecl:'Лига конференций',coppa_italia:'Кубок Италии'};
  function __cw32ThemeClass(key){return key==='ucl'?'mc-theme-ucl':key==='uel'?'mc-theme-uel':key==='uecl'?'mc-theme-uecl':key==='coppa_italia'?'mc-theme-coppa':''}
  function __cw32ExternalCrest(team){const url=String(team?.crest_url||'').trim();return url?`<img class="logo mc-external-crest" loading="eager" decoding="async" fetchpriority="high" src="${esc(url)}" alt="">`:'<span class="logo">⚽</span>'}
  function __cw32ExternalHeroMeta(d){const comp=String(d?.competition||d?.match?.competition||''),label=__cw32CompetitionLabels[comp]||'Матч',stage=String(d?.stage?.label||d?.match?.stage_label||'').trim();return {comp,label,stage,text:label+(stage?' · '+stage:'')}}

  const __cw32MatchHtmlBase=matchCenterHtml;
  matchCenterHtml=function(d){
    let html=__cw32MatchHtmlBase(d),source=String(d?.source||d?.match?.source||'serie_a');
    if(source!=='external')return html;
    const m=d?.match||{},meta=__cw32ExternalHeroMeta(d),theme=__cw32ThemeClass(meta.comp),shellClass=`mc-shell ${theme}`.trim();
    html=html.replace('<div class="mc-shell">',`<div class="${shellClass}" data-mc-source="external" data-mc-competition="${esc(meta.comp)}">`);
    const logos=[__cw32ExternalCrest(m.home),__cw32ExternalCrest(m.away)];let logoIndex=0;
    html=html.replace(/<span class="logo">⚽<\/span>/g,()=>logos[logoIndex++]||'<span class="logo">⚽</span>');
    html=html.replace(/<div class="mc-kickoff">[\s\S]*?<\/div>/,`<div class="mc-kickoff mc-external-meta"><b>${esc(meta.text)}</b><span>${esc(fmt(m.kickoff_at))}</span></div>`);
    const rawStatus=String(m?.live_status||'').toLowerCase();
    if(rawStatus==='postponed')html=html.replace(/(<span class="mc-status[^>]*>)[\s\S]*?(<\/span>)/,'$1Перенесён$2');
    if(rawStatus==='cancelled')html=html.replace(/(<span class="mc-status[^>]*>)[\s\S]*?(<\/span>)/,'$1Отменён$2');
    return html
  };

  if(typeof __cwMtMatchCardHtml==='function'){
    const __cw32MtCardBase=__cwMtMatchCardHtml;
    __cwMtMatchCardHtml=function(match){const html=__cw32MtCardBase(match),id=esc(String(match?.matchId||''));return html.replace('<article ',`<article data-external-match-id="${id}" data-match-source="external" `)};
  }
  if(typeof __cwPredExternalEditCard==='function'){
    const __cw32PredEditBase=__cwPredExternalEditCard;
    __cwPredExternalEditCard=function(match){const html=__cw32PredEditBase(match),id=esc(String(match?.matchId||''));return html.replace('<article ',`<article data-external-match-id="${id}" data-match-source="external" `)};
  }
  if(typeof __cwPredExternalMineCard==='function'){
    const __cw32PredMineBase=__cwPredExternalMineCard;
    __cwPredExternalMineCard=function(match){const html=__cw32PredMineBase(match),id=esc(String(match?.matchId||''));return html.replace('<article ',`<article data-external-match-id="${id}" data-match-source="external" `)};
  }

  let __cw32MatchReturnState=null;
  function __cw32CaptureReturn(){return {scroll:Number(main?.scrollTop)||0,mtCompetition:typeof __cwMtCompetition==='string'?__cwMtCompetition:'',mtStage:typeof __cwMtStageKey==='string'?__cwMtStageKey:'',predCompetition:typeof __cwPredCompetition==='string'?__cwPredCompetition:'',predStage:typeof __cwPredStageKey==='string'?__cwPredStageKey:'',predMode:typeof __cwPredMode==='string'?__cwPredMode:'edit'}}
  function __cw32RestoreListState(snap){if(!snap)return;try{if(typeof __cwMtCompetition!=='undefined')__cwMtCompetition=snap.mtCompetition||'';if(typeof __cwMtStageKey!=='undefined')__cwMtStageKey=snap.mtStage||'';if(typeof __cwPredCompetition!=='undefined')__cwPredCompetition=snap.predCompetition||'';if(typeof __cwPredStageKey!=='undefined')__cwPredStageKey=snap.predStage||'';if(typeof __cwPredMode!=='undefined')__cwPredMode=snap.predMode||'edit'}catch(_e){}}
  const __cw32OpenMatchBase=openMatchCenter;
  openMatchCenter=async function(id,source=matchViewSource){
    const normalized=String(source||'serie_a')==='external'?'external':'serie_a';
    if(!matchViewId)__cw32MatchReturnState=__cw32CaptureReturn();
    matchViewSource=normalized;
    return await __cw32OpenMatchBase(Number(id))
  };
  const __cw32CloseMatchBase=closeMatchCenter;
  closeMatchCenter=function(...args){
    const snap=__cw32MatchReturnState;__cw32RestoreListState(snap);
    const result=__cw32CloseMatchBase(...args);
    __cw32MatchReturnState=null;matchViewSource='serie_a';
    if(snap)requestAnimationFrame(()=>{if(main)main.scrollTop=Number(snap.scroll)||0});
    return result
  };

  const __cw32BindBase=bind;
  bind=function(){
    const result=__cw32BindBase();
    root.querySelectorAll('.cwmt-match-card[data-cwmt-match]').forEach(card=>{
      card.onclick=null;
      if(card.dataset.cw32MatchCenterBound==='1')return;card.dataset.cw32MatchCenterBound='1';
      card.addEventListener('click',e=>{if(e.target.closest?.('button,[data-cwmt-local-club],[data-cwmt-stage],[data-cwmt-action]'))return;const id=Number(card.getAttribute('data-cwmt-match'));if(id>0)openMatchCenter(id,'external')});
    });
    root.querySelectorAll('.cwpred-external-card[data-cwpred-match]').forEach(card=>{
      if(card.dataset.cw32MatchCenterBound==='1')return;card.dataset.cw32MatchCenterBound='1';
      card.addEventListener('click',e=>{if(e.target.closest?.('.cw29-score-pick,#cw29-score-picker,button,[data-cwpred-action],[data-cwpred-pick]'))return;const id=Number(card.getAttribute('data-cwpred-match'));if(id>0)openMatchCenter(id,'external')});
    });
    return result
  };
  /* /ciao-v32-external-match-center-20260908 */
'''

tail = '/* ===== /Ciao, Web! v22.5 product polish layer ===== */'
if s.count(tail) != 1:
    raise SystemExit(f'tail marker count {s.count(tail)}')
if 'ciao-v32-external-match-center-20260908' in s:
    raise SystemExit('v32 code already present')
s = s.replace(tail, block + '\n\n' + tail, 1)

p.write_text(s)
print('v32 patch applied')
