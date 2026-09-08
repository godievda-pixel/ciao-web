from pathlib import Path
import sys

PATH=Path('index.html')
MARK='ciao-v31-premium-predictor-profile-20260908'
STYLE_ID='cw31-predictor-style'
ANCHOR='  /* /ciao-v30-premium-rating-20260908 */\n'

CSS='''
<style id="cw31-predictor-style">
#ciao-miniapp-root.cw31-profile-open .header,#ciao-miniapp-root.cw31-profile-open .content,#ciao-miniapp-root.cw31-profile-open .nav{pointer-events:none!important}
#ciao-miniapp-root .cw31-profile{--cw30-accent:#3764ff;--cw30-accent-rgb:55,100,255;--cw30-soft:#a7b8ff;--cw30-glow:rgba(55,100,255,.25);position:fixed;inset:0;z-index:2147481200;background:radial-gradient(circle at 85% 4%,var(--cw30-glow),transparent 27%),linear-gradient(180deg,#050b1b,#030817 54%,#020611);color:#f8fbff;display:flex;flex-direction:column;overscroll-behavior:contain}
#ciao-miniapp-root .cw31-profile.cw30-theme-serie_a{--cw30-accent:#35a7ff;--cw30-accent-rgb:53,167,255;--cw30-soft:#a9dcff;--cw30-glow:rgba(53,167,255,.23)}
#ciao-miniapp-root .cw31-profile.cw30-theme-ucl{--cw30-accent:#756cff;--cw30-accent-rgb:117,108,255;--cw30-soft:#c1bdff;--cw30-glow:rgba(117,108,255,.28)}
#ciao-miniapp-root .cw31-profile.cw30-theme-uel{--cw30-accent:#ff8b24;--cw30-accent-rgb:255,139,36;--cw30-soft:#ffd0a5;--cw30-glow:rgba(255,139,36,.22)}
#ciao-miniapp-root .cw31-profile.cw30-theme-uecl{--cw30-accent:#39d183;--cw30-accent-rgb:57,209,131;--cw30-soft:#a6efc8;--cw30-glow:rgba(57,209,131,.20)}
#ciao-miniapp-root .cw31-profile.cw30-theme-coppa_italia{--cw30-accent:#4d8dff;--cw30-accent-rgb:77,141,255;--cw30-soft:#b8d0ff;--cw30-glow:rgba(77,141,255,.22)}
#ciao-miniapp-root .cw31-profile-toolbar{flex:0 0 auto;display:grid;grid-template-columns:42px 1fr 42px;align-items:center;padding:calc(8px + env(safe-area-inset-top,0px)) 12px 9px;border-bottom:1px solid rgba(255,255,255,.055);background:rgba(3,8,23,.80);backdrop-filter:blur(22px) saturate(130%)}
#ciao-miniapp-root .cw31-profile-back{appearance:none;width:38px;height:38px;border:1px solid rgba(255,255,255,.07);border-radius:12px;background:rgba(255,255,255,.045);color:#fff;font-size:22px;line-height:1;display:grid;place-items:center}
#ciao-miniapp-root .cw31-profile-toolbar b{text-align:center;font-family:'Unbounded','Manrope',sans-serif;font-size:12px;letter-spacing:-.025em}
#ciao-miniapp-root .cw31-profile-scroll{flex:1 1 auto;min-height:0;overflow-y:auto;overscroll-behavior:contain;-webkit-overflow-scrolling:touch;padding:12px 14px calc(24px + env(safe-area-inset-bottom,0px));scrollbar-width:none}
#ciao-miniapp-root .cw31-profile-scroll::-webkit-scrollbar{display:none}
#ciao-miniapp-root .cw31-profile-body{max-width:760px;margin:0 auto;display:grid;gap:12px}
#ciao-miniapp-root .cw31-profile-hero{position:relative;overflow:hidden;border-radius:22px;padding:18px 15px 15px;border:1px solid rgba(var(--cw30-accent-rgb),.23);background:linear-gradient(135deg,rgba(var(--cw30-accent-rgb),.17),rgba(9,19,45,.92) 48%,rgba(5,12,30,.97));box-shadow:0 18px 54px rgba(0,0,0,.30),inset 0 1px 0 rgba(255,255,255,.04)}
#ciao-miniapp-root .cw31-profile-hero:after{content:'';position:absolute;width:175px;height:175px;border-radius:50%;right:-72px;top:-91px;background:radial-gradient(circle,var(--cw30-glow),transparent 69%);pointer-events:none}
#ciao-miniapp-root .cw31-profile-identity{position:relative;z-index:1;display:flex;align-items:center;gap:11px;min-width:0}
#ciao-miniapp-root .cw31-profile-logo{width:43px!important;height:43px!important;flex:0 0 43px!important;object-fit:contain;filter:drop-shadow(0 8px 16px rgba(0,0,0,.28))}
#ciao-miniapp-root .cw31-profile-avatar-fallback{width:43px;height:43px;flex:0 0 43px;border-radius:14px;display:grid;place-items:center;background:rgba(var(--cw30-accent-rgb),.16);border:1px solid rgba(var(--cw30-accent-rgb),.20);font:800 16px/1 'Unbounded','Manrope',sans-serif;color:var(--cw30-soft)}
#ciao-miniapp-root .cw31-profile-name{min-width:0}
#ciao-miniapp-root .cw31-profile-name h2{margin:0;font-family:'Unbounded','Manrope',sans-serif;font-size:17px;line-height:1.1;letter-spacing:-.035em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#ciao-miniapp-root .cw31-profile-name span{display:block;margin-top:5px;font-size:9px;font-weight:800;color:var(--cw30-soft);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#ciao-miniapp-root .cw31-profile-primary{position:relative;z-index:1;display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:15px}
#ciao-miniapp-root .cw31-profile-primary div{padding:10px 11px;border-radius:14px;border:1px solid rgba(255,255,255,.055);background:rgba(2,7,18,.25)}
#ciao-miniapp-root .cw31-profile-primary b{display:block;font-family:'Unbounded','Manrope',sans-serif;font-size:20px;line-height:1}
#ciao-miniapp-root .cw31-profile-primary span{display:block;margin-top:5px;font-size:8px;font-weight:800;color:#8091b8;text-transform:uppercase;letter-spacing:.05em}
#ciao-miniapp-root .cw31-profile-comp-scroll{overflow-x:auto;scrollbar-width:none;margin:0 -14px;padding:0 14px}
#ciao-miniapp-root .cw31-profile-comp-scroll::-webkit-scrollbar{display:none}
#ciao-miniapp-root .cw31-profile-compbar{display:flex;width:max-content;min-width:100%;gap:7px}
#ciao-miniapp-root .cw31-profile-comp{appearance:none;min-height:35px;padding:0 11px;border-radius:12px;border:1px solid rgba(255,255,255,.06);background:rgba(255,255,255,.035);color:#8999bd;font:850 9.5px/1 'Manrope',sans-serif;white-space:nowrap}
#ciao-miniapp-root .cw31-profile-comp.active{color:#fff;border-color:rgba(var(--cw30-accent-rgb),.36);background:rgba(var(--cw30-accent-rgb),.18);box-shadow:0 8px 22px var(--cw30-glow)}
#ciao-miniapp-root .cw31-profile-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px}
#ciao-miniapp-root .cw31-profile-metric{min-width:0;padding:10px 7px;border-radius:14px;border:1px solid rgba(255,255,255,.055);background:linear-gradient(180deg,rgba(14,27,61,.74),rgba(7,16,38,.78));text-align:center}
#ciao-miniapp-root .cw31-profile-metric b{display:block;font-size:14px;line-height:1;font-weight:950;color:#fff;white-space:nowrap}
#ciao-miniapp-root .cw31-profile-metric span{display:block;margin-top:5px;font-size:7px;line-height:1.1;font-weight:800;color:#7f91b8}
#ciao-miniapp-root .cw31-recent{display:flex;gap:7px;overflow:hidden;padding:9px 10px;border-radius:14px;border:1px solid rgba(var(--cw30-accent-rgb),.12);background:rgba(var(--cw30-accent-rgb),.055);font-size:8px;font-weight:800;color:#8798bd}
#ciao-miniapp-root .cw31-recent b{color:var(--cw30-soft);font-weight:900}
#ciao-miniapp-root .cw31-section-head{display:flex;align-items:flex-end;justify-content:space-between;padding:2px 2px 0;gap:10px}
#ciao-miniapp-root .cw31-section-head h3{margin:0;font-family:'Unbounded','Manrope',sans-serif;font-size:12px;letter-spacing:-.025em}
#ciao-miniapp-root .cw31-section-head span{font-size:8px;color:#7183aa;font-weight:800}
#ciao-miniapp-root .cw31-history-list{display:grid;gap:7px}
#ciao-miniapp-root .cw31-history-row{border:1px solid rgba(255,255,255,.06);border-radius:16px;padding:11px;background:linear-gradient(180deg,rgba(12,24,55,.82),rgba(7,15,35,.90));position:relative;overflow:hidden}
#ciao-miniapp-root .cw31-history-row.exact{border-color:rgba(226,189,83,.22);background:linear-gradient(110deg,rgba(210,169,61,.095),rgba(8,18,42,.90) 38%)}
#ciao-miniapp-root .cw31-history-row.success{border-color:rgba(var(--cw30-accent-rgb),.18)}
#ciao-miniapp-root .cw31-history-top{display:flex;justify-content:space-between;align-items:center;gap:9px;font-size:7.5px;font-weight:850;color:#7183a9;text-transform:uppercase;letter-spacing:.045em}
#ciao-miniapp-root .cw31-history-row.exact .cw31-history-comp{color:#e6c66e}.cw31-history-row.success .cw31-history-comp{color:var(--cw30-soft)}
#ciao-miniapp-root .cw31-history-match{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);gap:7px;align-items:center;margin-top:9px}
#ciao-miniapp-root .cw31-history-team{font-size:10px;font-weight:900;color:#eef3ff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.cw31-history-team.away{text-align:right}
#ciao-miniapp-root .cw31-history-final{font-family:'Unbounded','Manrope',sans-serif;font-size:12px;font-weight:800;white-space:nowrap;color:#fff}
#ciao-miniapp-root .cw31-history-bottom{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:8px;padding-top:8px;border-top:1px solid rgba(255,255,255,.045)}
#ciao-miniapp-root .cw31-history-pred{font-size:8px;font-weight:800;color:#8092b9}.cw31-history-pred b{color:#eef3ff;font-size:10px;margin-left:4px}
#ciao-miniapp-root .cw31-history-points{font:900 10px/1 'Unbounded','Manrope',sans-serif;color:#8ea3ca}.cw31-history-row.exact .cw31-history-points{color:#e8ca73}.cw31-history-row.success .cw31-history-points{color:var(--cw30-soft)}
#ciao-miniapp-root .cw31-more{appearance:none;width:100%;min-height:42px;border-radius:13px;border:1px solid rgba(var(--cw30-accent-rgb),.18);background:rgba(var(--cw30-accent-rgb),.09);color:#fff;font:850 10px/1 'Manrope',sans-serif}
#ciao-miniapp-root .cw31-more[disabled]{opacity:.55}
#ciao-miniapp-root .cw31-profile-empty{padding:18px 12px;border-radius:16px;border:1px solid rgba(255,255,255,.055);background:rgba(255,255,255,.025);text-align:center;color:#788ab1;font-size:9px;font-weight:800}
#ciao-miniapp-root .cw31-profile-error{padding:18px 12px;border-radius:16px;border:1px solid rgba(255,99,124,.16);background:rgba(255,76,108,.065);text-align:center;color:#ffc2cc;font-size:9px;font-weight:800}
#ciao-miniapp-root .cw31-profile-error button{display:block;margin:10px auto 0;border:0;border-radius:10px;background:rgba(255,255,255,.09);color:#fff;font:800 9px/1 'Manrope',sans-serif;padding:9px 13px}
#ciao-miniapp-root .cw31-profile-skeleton{display:grid;gap:9px}.cw31-profile-skeleton i{display:block;height:56px;border-radius:15px;background:rgba(255,255,255,.035);position:relative;overflow:hidden}.cw31-profile-skeleton i:after{content:'';position:absolute;inset:0;transform:translateX(-110%);background:linear-gradient(90deg,transparent,rgba(255,255,255,.07),transparent);animation:cw22Shimmer 1.05s linear infinite}
@media(max-width:390px){#ciao-miniapp-root .cw31-profile-scroll{padding-left:12px;padding-right:12px}#ciao-miniapp-root .cw31-profile-metrics{gap:5px}#ciao-miniapp-root .cw31-profile-metric{padding:9px 5px}#ciao-miniapp-root .cw31-profile-metric b{font-size:13px}#ciao-miniapp-root .cw31-profile-metric span{font-size:6.6px}#ciao-miniapp-root .cw31-history-row{padding:10px}#ciao-miniapp-root .cw31-history-match{gap:5px}#ciao-miniapp-root .cw31-history-team{font-size:9px}}
@media(prefers-reduced-motion:reduce){#ciao-miniapp-root .cw31-profile-skeleton i:after{animation:none}}
</style>
'''

JS='''
  /* ciao-v31-premium-predictor-profile-20260908 */
  let __cw31PredictorId=0;
  let __cw31PredictorCompetition='all';
  let __cw31PredictorData=null;
  let __cw31PredictorLoading=false;
  let __cw31PredictorMoreLoading=false;
  let __cw31PredictorError='';
  let __cw31PredictorRequestVersion=0;
  let __cw31RatingScroll=0;
  function __cw31Date(v){const t=Date.parse(String(v||''));if(!Number.isFinite(t))return '—';try{return new Intl.DateTimeFormat('ru-RU',{day:'2-digit',month:'2-digit'}).format(new Date(t))}catch(_e){return '—'}}
  function __cw31Initial(v){const s=String(v||'').trim();return (s[0]||'?').toUpperCase()}
  function __cw31ProfileCompBar(){return `<div class="cw31-profile-comp-scroll"><div class="cw31-profile-compbar">${__cw30RatingOrder.map(k=>`<button type="button" class="cw31-profile-comp ${k===__cw31PredictorCompetition?'active':''}" data-cw31-comp="${k}">${__cw30RatingLabels[k]}</button>`).join('')}</div></div>`}
  function __cw31Metric(v,l){return `<div class="cw31-profile-metric"><b>${v??0}</b><span>${l}</span></div>`}
  function __cw31HistoryRow(h){const q=['exact','success','miss'].includes(String(h?.quality))?String(h.quality):'miss';return `<article class="cw31-history-row ${q}" data-cw31-history-key="${esc(String(h?.key||''))}"><div class="cw31-history-top"><span class="cw31-history-comp">${esc(h?.competition_label||__cw30RatingLabels[h?.competition]||'Матч')}</span><span>${__cw31Date(h?.settled_at)}</span></div><div class="cw31-history-match"><span class="cw31-history-team">${esc(h?.home_name||'—')}</span><b class="cw31-history-final">${Number(h?.final_home)||0}:${Number(h?.final_away)||0}</b><span class="cw31-history-team away">${esc(h?.away_name||'—')}</span></div><div class="cw31-history-bottom"><span class="cw31-history-pred">Прогноз <b>${Number(h?.prediction_home)||0}:${Number(h?.prediction_away)||0}</b></span><span class="cw31-history-points">+${Number(h?.points)||0}</span></div></article>`}
  function __cw31HistoryRows(rows){return (Array.isArray(rows)?rows:[]).map(__cw31HistoryRow).join('')}
  function __cw31MoreHtml(){const page=__cw31PredictorData?.history_page;if(!page?.has_more)return '';return `<button type="button" class="cw31-more" data-cw31-more ${__cw31PredictorMoreLoading?'disabled':''}>${__cw31PredictorMoreLoading?'Загружаем…':'Показать ещё'}</button>`}
  function __cw31ProfileDataHtml(){const p=__cw31PredictorData;if(__cw31PredictorLoading&&!p)return `<div class="cw31-profile-skeleton">${Array.from({length:5},()=>'<i></i>').join('')}</div>`;if(__cw31PredictorError&&!p)return `<div class="cw31-profile-error">Не удалось загрузить профиль<button type="button" data-cw31-retry>Повторить</button></div>`;if(!p)return '';const s=p.stats||{},r=p.recent_summary||{},logo=p.favorite_team&&typeof __cw18Logo==='function'?__cw18Logo(p.favorite_team,'cw31-profile-logo'):`<span class="cw31-profile-avatar-fallback">${esc(__cw31Initial(p.display_name))}</span>`,history=Array.isArray(p.history)?p.history:[];return `<div class="cw31-profile-hero"><div class="cw31-profile-identity">${logo}<div class="cw31-profile-name"><h2>${esc(p.display_name||'Прогнозист')}</h2><span>${p.favorite_team?esc(p.favorite_team.name):'Любимый клуб не выбран'}</span></div></div><div class="cw31-profile-primary"><div><b>${s.rank??'—'}</b><span>Место</span></div><div><b>${Number(s.points)||0}</b><span>Очки</span></div></div></div>${__cw31ProfileCompBar()}<div class="cw31-profile-metrics">${__cw31Metric(Number(s.exact)||0,'Точные')}${__cw31Metric((Number(s.success_rate)||0)+'%','Успешность')}${__cw31Metric(Number(s.streak)||0,'Серия')}${__cw31Metric(__cw30Trend(s.trend),'Динамика')}</div><div class="cw31-recent"><span>Последние <b>${Number(r.sample_size)||0}</b></span><span>точных <b>${Number(r.exact)||0}</b></span><span>успешных <b>${Number(r.successful)||0}</b></span><span><b>${Number(r.points)||0}</b> очков</span></div><div class="cw31-section-head"><h3>История прогнозов</h3><span>только завершённые</span></div>${history.length?`<div class="cw31-history-list">${__cw31HistoryRows(history)}</div>`:'<div class="cw31-profile-empty">Завершённых прогнозов в этом турнире пока нет</div>'}<div data-cw31-more-slot>${__cw31MoreHtml()}</div>`}
  function __cw31OverlayHtml(){return `<section class="cw31-profile cw30-theme-${__cw31PredictorCompetition}" data-cw31-overlay><div class="cw31-profile-toolbar"><button type="button" class="cw31-profile-back" data-cw31-close aria-label="Назад">‹</button><b>Профиль прогнозиста</b><span></span></div><div class="cw31-profile-scroll" data-cw31-scroll><div class="cw31-profile-body" data-cw31-body>${__cw31ProfileDataHtml()}</div></div></section>`}
  function __cw31Mount(){root.querySelector('[data-cw31-overlay]')?.remove();root.insertAdjacentHTML('beforeend',__cw31OverlayHtml());root.classList.add('cw31-profile-open')}
  function __cw31PatchBody({keepScroll=false}={}){const scroll=root.querySelector('[data-cw31-scroll]'),y=keepScroll?Number(scroll?.scrollTop)||0:0,body=root.querySelector('[data-cw31-body]');if(body)body.innerHTML=__cw31ProfileDataHtml();const ov=root.querySelector('[data-cw31-overlay]');if(ov){ov.className=`cw31-profile cw30-theme-${__cw31PredictorCompetition}`}if(scroll)requestAnimationFrame(()=>{scroll.scrollTop=y})}
  async function __cw31FetchProfile({cursor=null,append=false}={}){if(!__cw31PredictorId)return false;const version=++__cw31PredictorRequestVersion,competition=__cw31PredictorCompetition;if(append){if(__cw31PredictorMoreLoading)return false;__cw31PredictorMoreLoading=true;const slot=root.querySelector('[data-cw31-more-slot]');if(slot)slot.innerHTML=__cw31MoreHtml()}else{__cw31PredictorLoading=true;__cw31PredictorError='';__cw31PredictorData=null;__cw31PatchBody()}try{const r=await __cw18Post({action:'public_predictor',user_id:__cw31PredictorId,competition,history_limit:20,history_cursor:cursor});if(version!==__cw31PredictorRequestVersion||competition!==__cw31PredictorCompetition)return false;const next=r?.predictor;if(!next)throw new Error('profile_payload_missing');if(append){const existing=Array.isArray(__cw31PredictorData?.history)?__cw31PredictorData.history:[],seen=new Set(existing.map(x=>String(x?.key||''))),incoming=(Array.isArray(next.history)?next.history:[]).filter(x=>!seen.has(String(x?.key||'')));__cw31PredictorData={...__cw31PredictorData,history:existing.concat(incoming),history_page:next.history_page||{next_cursor:null,has_more:false}};const list=root.querySelector('.cw31-history-list');if(list&&incoming.length)list.insertAdjacentHTML('beforeend',__cw31HistoryRows(incoming));const slot=root.querySelector('[data-cw31-more-slot]');__cw31PredictorMoreLoading=false;if(slot)slot.innerHTML=__cw31MoreHtml();return true}__cw31PredictorData=next;__cw31PredictorLoading=false;__cw31PatchBody();return true}catch(e){if(version!==__cw31PredictorRequestVersion)return false;if(append){__cw31PredictorMoreLoading=false;const slot=root.querySelector('[data-cw31-more-slot]');if(slot)slot.innerHTML='<button type="button" class="cw31-more" data-cw31-more>Не удалось загрузить · повторить</button>';return false}__cw31PredictorLoading=false;__cw31PredictorError=String(e?.message||'profile_failed');__cw31PatchBody();return false}}
  function __cw31OpenPredictor(id,competition=__cw30RatingCompetition){id=Number(id);if(!id)return;__cw31RatingScroll=Number(main?.scrollTop)||0;__cw31PredictorId=id;__cw31PredictorCompetition=__cw30RatingOrder.includes(String(competition))?String(competition):'all';__cw31PredictorData=null;__cw31PredictorError='';__cw31Mount();__cw31FetchProfile()}
  function __cw31ClosePredictor(){__cw31PredictorRequestVersion++;__cw31PredictorId=0;__cw31PredictorData=null;__cw31PredictorError='';root.querySelector('[data-cw31-overlay]')?.remove();root.classList.remove('cw31-profile-open');requestAnimationFrame(()=>{if(main)main.scrollTop=__cw31RatingScroll})}
  async function __cw31SwitchCompetition(k){if(!__cw30RatingOrder.includes(String(k))||k===__cw31PredictorCompetition)return;__cw31PredictorCompetition=String(k);__cw31PredictorData=null;__cw31PredictorError='';__cw31PredictorLoading=true;__cw31PatchBody();await __cw31FetchProfile()}
  async function __cw31LoadMore(){const cursor=__cw31PredictorData?.history_page?.next_cursor;if(!cursor)return;await __cw31FetchProfile({cursor,append:true})}
  const __cw31ProfileBaseBind=bind;
  bind=function(){__cw31ProfileBaseBind();root.querySelectorAll('[data-cw30-predictor]').forEach(b=>b.onclick=()=>__cw31OpenPredictor(Number(b.dataset.cw30Predictor),__cw30RatingCompetition))};
  if(!root.dataset.cw31ProfileBound){root.dataset.cw31ProfileBound='1';root.addEventListener('click',e=>{const close=e.target.closest?.('[data-cw31-close]');if(close){e.preventDefault();__cw31ClosePredictor();return}const comp=e.target.closest?.('[data-cw31-comp]');if(comp){e.preventDefault();__cw31SwitchCompetition(String(comp.dataset.cw31Comp||'all'));return}const more=e.target.closest?.('[data-cw31-more]');if(more){e.preventDefault();__cw31LoadMore();return}const retry=e.target.closest?.('[data-cw31-retry]');if(retry){e.preventDefault();__cw31FetchProfile();return}})}
  /* /ciao-v31-premium-predictor-profile-20260908 */
'''

def red(html):
    if MARK in html: raise SystemExit('RED failed: predictor profile already present')
    if 'ciao-v30-premium-rating-20260908' not in html: raise SystemExit('RED invalid: v30 Rating prerequisite missing')
    print('RED observed: premium predictor profile absent')

def apply(html):
    if MARK in html: raise SystemExit('profile marker already present')
    if html.count(ANCHOR)!=1: raise SystemExit(f'v30 anchor count={html.count(ANCHOR)}')
    if f'id="{STYLE_ID}"' in html: raise SystemExit('profile style already present')
    html=html.replace('</head>',CSS+'\n</head>',1)
    html=html.replace(ANCHOR,ANCHOR+JS,1)
    PATH.write_text(html,encoding='utf-8')
    print('applied premium predictor profile patch')

def green(html):
    required=[
      MARK,'cw31-profile-scroll','История прогнозов','Показать ещё','history_cursor:cursor',
      "action:'public_predictor',user_id:__cw31PredictorId,competition",
      '__cw31RatingScroll','main.scrollTop=__cw31RatingScroll','data-cw31-more','data-cw31-comp',
      '__cw31OpenPredictor(Number(b.dataset.cw30Predictor),__cw30RatingCompetition)',
      'data-cw31-history-key','final_home','prediction_home','quality',
      'root.classList.add(\'cw31-profile-open\')'
    ]
    missing=[x for x in required if x not in html]
    if missing: raise SystemExit('GREEN missing: '+', '.join(missing))
    block=html.split('/* ciao-v31-premium-predictor-profile-20260908 */',1)[1].split('/* /ciao-v31-premium-predictor-profile-20260908 */',1)[0]
    if "action:'public_predictor',user_id:Number(id)" in block: raise SystemExit('legacy public profile request leaked into v31 block')
    if 'openClubProfile' in block or 'data-club-id' in block: raise SystemExit('club navigation leaked into predictor profile')
    print('GREEN predictor profile contract: PASS')

html=PATH.read_text(encoding='utf-8')
mode=sys.argv[1] if len(sys.argv)>1 else 'green'
if mode=='red': red(html)
elif mode=='apply': apply(html)
elif mode=='green': green(html)
else: raise SystemExit('usage: cw32_predictor_profile.py red|apply|green')
