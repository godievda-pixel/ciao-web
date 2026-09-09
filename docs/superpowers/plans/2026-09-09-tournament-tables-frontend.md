# Tournament Tables Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing `Таблицы` tab into a five-tournament premium hub with full UEFA tables and a horizontally swipeable Coppa Italia bracket, while preserving the existing Serie A table and all current app flows.

**Architecture:** Add one late-loaded compatibility layer to the existing single-file `index.html`, after current navigation/Match Center layers, so existing behavior remains the base implementation. Capture the current `serieA`, `bind`, and Serie A refresh functions, then route only `tab==='seriea'` through the new tables controller. External data comes only from `ciao-tournament-tables-v1`; club navigation uses existing `openClubProfile(local_team_id)` and Coppa match navigation uses existing `openMatchCenter(external_match_id,'external')`.

**Tech Stack:** Existing vanilla HTML/CSS/JavaScript single-file app, Supabase Edge Function fetch, current premium loading CSS, existing Ciao club profile and external Match Center navigation.

**Spec:** `docs/superpowers/specs/2026-09-09-tournament-tables-design.md`

## Global Constraints

- Final production `main` contains root `index.html` only; implementation tests/tools stay on the feature branch and are not merged into `main`.
- Do not change `cw29` score picker, Predictions, Matches, Rating, Match Center APIs, or the 5-second live scheduler.
- `Таблицы` contains exactly five competition choices: Serie A, Coppa Italia, Champions League, Europa League, Conference League.
- UEFA tables render all 36 rows with no global horizontal page scroll.
- Only rows with numeric `local_team_id` expose club-profile interaction.
- Every real Coppa event with numeric `external_match_id` opens existing full Match Center with source `external`.
- Shared Italian premium loading system is reused during fetch.
- Foreign club rows have no link affordance.
- Existing Serie A renderer and live update logic remain the source of truth for Serie A.

---

### Task 1: Add frontend contract tests and the tables controller shell

**Files:**
- Modify on feature branch: `index.html` after the latest production compatibility layer, before the closing app script.
- Create on feature branch only: `work/tournament-tables/frontend/tests/tables-contract.py`

**Interfaces:**
- Consumes current global functions/variables: `serieA`, `bind`, `render`, `tab`, `main`, `root`, `initData`, `openClubProfile`, `openMatchCenter`.
- Produces:
  - `__cwTblCompetition`
  - `__cwTblPayload`
  - `__cwTblSelect(key)`
  - `__cwTblHubHtml()`
  - `__cwTblScreenHtml()`
  - marker `ciao-v34-tournament-tables-20260909`.

- [ ] **Step 1: Write the failing static contract test**

```python
from pathlib import Path

s = Path('index.html').read_text()
assert 'ciao-v34-tournament-tables-20260909' in s
assert "const __CWTBL_API='https://dkefzepiiudehhzbbrjn.supabase.co/functions/v1/ciao-tournament-tables-v1'" in s
assert "data-cwtbl-competition=\"serie_a\"" in s
assert "data-cwtbl-competition=\"coppa_italia\"" in s
assert "data-cwtbl-competition=\"ucl\"" in s
assert "data-cwtbl-competition=\"uel\"" in s
assert "data-cwtbl-competition=\"uecl\"" in s
assert 'ciao-v29-native-score-picker-20260908' in s
assert '__CW2014_LIVE_MS=5000' in s
```

- [ ] **Step 2: Run RED**

```bash
python work/tournament-tables/frontend/tests/tables-contract.py
```

Expected: FAIL on the new marker/API.

- [ ] **Step 3: Add the controller state and hub**

Append one clearly delimited layer:

```js
/* ===== ciao-v34-tournament-tables-20260909 ===== */
const __CWTBL_API='https://dkefzepiiudehhzbbrjn.supabase.co/functions/v1/ciao-tournament-tables-v1';
const __cwTblLegacySerieA=serieA;
const __cwTblLegacyBind=bind;
let __cwTblCompetition='',__cwTblPayload=null,__cwTblLoading=false,__cwTblError='',__cwTblRequestVersion=0,__cwTblTimer=null;
const __cwTblMeta={
  serie_a:{title:'Серия А',theme:'serie-a',wide:true},
  coppa_italia:{title:'Кубок Италии',theme:'coppa'},
  ucl:{title:'Лига Чемпионов',theme:'champions'},
  uel:{title:'Лига Европы',theme:'europa'},
  uecl:{title:'Лига Конференций',theme:'conference'}
};
function __cwTblHubHtml(){
  return `<section class="cwtbl-hub"><div class="section-title"><h3>Таблицы</h3><span>5 турниров</span></div><div class="cwtbl-grid">
    <button type="button" class="cwtbl-card wide" data-cwtbl-competition="serie_a" data-cwtbl-theme="serie-a"><span>Серия А</span><i>→</i></button>
    <button type="button" class="cwtbl-card" data-cwtbl-competition="coppa_italia" data-cwtbl-theme="coppa"><span>Кубок Италии</span><i>→</i></button>
    <button type="button" class="cwtbl-card" data-cwtbl-competition="ucl" data-cwtbl-theme="champions"><span>Лига Чемпионов</span><i>→</i></button>
    <button type="button" class="cwtbl-card" data-cwtbl-competition="uel" data-cwtbl-theme="europa"><span>Лига Европы</span><i>→</i></button>
    <button type="button" class="cwtbl-card" data-cwtbl-competition="uecl" data-cwtbl-theme="conference"><span>Лига Конференций</span><i>→</i></button>
  </div></section>`;
}
function __cwTblScreenHtml(){if(!__cwTblCompetition)return __cwTblHubHtml();if(__cwTblCompetition==='serie_a')return __cwTblCover('serie_a')+__cwTblLegacySerieA();return __cwTblExternalHtml()}
serieA=function(){return __cwTblScreenHtml()};
```

`__cwTblCover(key)` renders a back button with `data-cwtbl-back` and competition title.

- [ ] **Step 4: Add controller binding**

```js
bind=function(){
  __cwTblLegacyBind();
  main?.querySelectorAll?.('[data-cwtbl-competition]').forEach(b=>b.addEventListener('click',()=>__cwTblSelect(String(b.dataset.cwtblCompetition||''))));
  main?.querySelector?.('[data-cwtbl-back]')?.addEventListener('click',()=>{__cwTblCompetition='';__cwTblPayload=null;__cwTblError='';__cwTblStopTimer();render()});
};
```

`__cwTblSelect('serie_a')` only sets state and renders. External competitions set loading state, render immediately, then call `__cwTblLoad(key)`.

- [ ] **Step 5: Add hub/cover theme CSS**

Use CSS variables and existing tournament palette:

```css
#ciao-miniapp-root[data-cwtbl-theme="champions"]{--cwtbl-a:#5367e6;--cwtbl-b:#49318f;--cwtbl-rgb:83,103,230}
#ciao-miniapp-root[data-cwtbl-theme="europa"]{--cwtbl-a:#e66a13;--cwtbl-b:#7a2c05;--cwtbl-rgb:230,106,19}
#ciao-miniapp-root[data-cwtbl-theme="conference"]{--cwtbl-a:#28a968;--cwtbl-b:#0b3b28;--cwtbl-rgb:40,169,104}
#ciao-miniapp-root[data-cwtbl-theme="coppa"]{--cwtbl-a:#159457;--cwtbl-b:#9f2435;--cwtbl-rgb:21,148,87}
#ciao-miniapp-root[data-cwtbl-theme="serie-a"]{--cwtbl-a:#3150ff;--cwtbl-b:#0b2f88;--cwtbl-rgb:49,80,255}
```

Cards use premium radial glow + dark gradients, not tournament logos/artwork.

- [ ] **Step 6: Run contract and JS syntax tests**

```bash
python work/tournament-tables/frontend/tests/tables-contract.py
python - <<'PY'
from pathlib import Path
import re, subprocess, tempfile
s=Path('index.html').read_text()
for i,(attrs,js) in enumerate(re.findall(r'<script([^>]*)>(.*?)</script>',s,re.S|re.I)):
    if 'src=' in attrs.lower() or not js.strip(): continue
    p=Path(tempfile.gettempdir())/f'cwtbl-{i}.js'; p.write_text(js); subprocess.run(['node','--check',str(p)],check=True)
PY
```

Expected: PASS.

- [ ] **Step 7: Commit controller shell**

```bash
git add index.html work/tournament-tables/frontend/tests/tables-contract.py
git commit -m "feat: add tournament tables hub"
```

---

### Task 2: Implement authenticated external table loading and UEFA 36-row renderer

**Files:**
- Modify: `index.html` inside `ciao-v34-tournament-tables-20260909`.
- Modify: `work/tournament-tables/frontend/tests/tables-contract.py`

**Interfaces:**
- Consumes backend POST `standings`.
- Produces `__cwTblApi`, `__cwTblLoad`, `__cwTblUefaHtml`, `__cwTblUefaRow`.

- [ ] **Step 1: Extend the failing contract test**

Add assertions:

```python
assert "action:'standings'" in s
assert 'cwtbl-zone-direct' in s
assert 'cwtbl-zone-playoff' in s
assert 'cwtbl-zone-eliminated' in s
assert 'data-cwtbl-club' in s
assert 'rows.length!==36' in s
```

Run and confirm failure.

- [ ] **Step 2: Implement API request/version guard**

```js
async function __cwTblApi(action,competition){
  const r=await fetch(__CWTBL_API,{method:'POST',headers:{'content-type':'application/json','x-telegram-init-data':initData},body:JSON.stringify({action,competition})});
  const j=await r.json().catch(()=>({}));
  if(!r.ok||!j?.ok){const e=new Error(j?.error||'Не удалось загрузить таблицу');e.status=r.status;e.payload=j;throw e}
  return j;
}
async function __cwTblLoad(key,{quiet=false}={}){
  const version=++__cwTblRequestVersion,action=key==='coppa_italia'?'bracket':'standings';
  if(!quiet){__cwTblLoading=true;__cwTblError='';render()}
  try{const payload=await __cwTblApi(action,key);if(version!==__cwTblRequestVersion||key!==__cwTblCompetition)return;__cwTblPayload=payload;__cwTblError=''}
  catch(e){if(version===__cwTblRequestVersion&&key===__cwTblCompetition)__cwTblError=e.message||'Ошибка загрузки'}
  finally{if(version===__cwTblRequestVersion&&key===__cwTblCompetition){__cwTblLoading=false;render();__cwTblSchedule()}}
}
```

- [ ] **Step 3: Implement loading/error/stale shell**

`__cwTblExternalHtml()` must render, in order:

1. competition cover;
2. stale badge when `payload.stale===true`;
3. `<div class="cw-it-loading">Загружаем таблицу…</div>` while loading and no payload;
4. retry state with `data-cwtbl-retry` when error and no payload;
5. UEFA or Coppa content when payload exists.

When an error occurs but cached payload already exists, keep the content visible and add the subtle stale badge instead of replacing it.

- [ ] **Step 4: Implement the 36-row UEFA renderer**

```js
function __cwTblUefaRow(r){
  const local=Number(r?.local_team_id)||0,zone=String(r?.zone||'eliminated');
  const tag=local?'button':'div', attrs=local?` type="button" data-cwtbl-club="${local}"`:'';
  const crest=r?.crest_url?`<img loading="lazy" decoding="async" src="${esc(r.crest_url)}" alt="">`:'<span class="cwtbl-ball">⚽</span>';
  return `<${tag} class="cwtbl-row cwtbl-zone-${zone}${local?' local':''}"${attrs}><span class="cwtbl-pos">${Number(r.position)||'—'}</span><span class="cwtbl-team">${crest}<span><b>${esc(r.name||'Команда')}</b><small>${Number(r.won)||0}-${Number(r.drawn)||0}-${Number(r.lost)||0} · ${Number(r.goals_for)||0}:${Number(r.goals_against)||0}</small></span></span><span>${Number(r.played)||0}</span><span>${Number(r.goal_difference)>0?'+':''}${Number(r.goal_difference)||0}</span><strong>${Number(r.points)||0}</strong></${tag}>`;
}
function __cwTblUefaHtml(payload){
  const rows=Array.isArray(payload?.rows)?payload.rows:[];
  if(rows.length!==36)return '<div class="cwtbl-error"><b>Таблица временно неполная</b><span>Обновим данные автоматически.</span></div>';
  return `<div class="cwtbl-table"><div class="cwtbl-head"><span>#</span><span>Команда</span><span>И</span><span>РМ</span><span>О</span></div>${rows.map(__cwTblUefaRow).join('')}</div><div class="cwtbl-legend"><span><i class="direct"></i>1–8 · 1/8 финала</span><span><i class="playoff"></i>9–24 · стыки</span><span><i class="eliminated"></i>25–36 · вылет</span></div>`;
}
```

- [ ] **Step 5: Add table CSS with no page-level horizontal overflow**

Core grid:

```css
#ciao-miniapp-root .cwtbl-head,#ciao-miniapp-root .cwtbl-row{display:grid;grid-template-columns:28px minmax(0,1fr) 28px 38px 32px;align-items:center;gap:6px}
#ciao-miniapp-root .cwtbl-table{width:100%;min-width:0;overflow:hidden;border:1px solid rgba(var(--cwtbl-rgb),.18);border-radius:20px;background:rgba(5,10,25,.72)}
#ciao-miniapp-root .cwtbl-team{min-width:0;display:flex;align-items:center;gap:8px;text-align:left}
#ciao-miniapp-root .cwtbl-team b{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#ciao-miniapp-root .cwtbl-row{width:100%;border:0;border-left:3px solid transparent;background:transparent;color:#f7f9ff;padding:9px 9px 9px 6px;font:inherit;text-align:inherit}
#ciao-miniapp-root .cwtbl-row.local{cursor:pointer;background:rgba(var(--cwtbl-rgb),.055)}
```

Zone tints remain subtle; use one thin left accent and very low-opacity row background.

- [ ] **Step 6: Wire only local club navigation**

In the bind override:

```js
main?.querySelectorAll?.('[data-cwtbl-club]').forEach(el=>el.addEventListener('click',ev=>{ev.preventDefault();ev.stopPropagation();const id=Number(el.dataset.cwtblClub);if(id)openClubProfile(id)}));
main?.querySelector?.('[data-cwtbl-retry]')?.addEventListener('click',()=>__cwTblLoad(__cwTblCompetition));
```

Foreign rows do not carry `data-cwtbl-club`, do not use `<button>`, and have no pointer styling.

- [ ] **Step 7: Run contracts/syntax and commit**

```bash
python work/tournament-tables/frontend/tests/tables-contract.py
# repeat inline node --check command from Task 1
git add index.html work/tournament-tables/frontend/tests/tables-contract.py
git commit -m "feat: add premium UEFA tables"
```

---

### Task 3: Implement the full Coppa Italia mobile bracket and Match Center navigation

**Files:**
- Modify: `index.html` in the tables layer.
- Modify: `work/tournament-tables/frontend/tests/tables-contract.py`

**Interfaces:**
- Consumes backend `rounds[]`, each actual event carrying numeric `external_match_id`.
- Produces `__cwTblCoppaHtml`, `__cwTblCoppaMatch`, `__cwTblFocusActiveRound`.

- [ ] **Step 1: Extend failing contract assertions**

```python
for key in ['r32','r16','qf','sf','final']:
    assert f"'{key}'" in s
assert 'scroll-snap-type:x mandatory' in s
assert 'data-cwtbl-match' in s
assert "openMatchCenter(id,'external')" in s
assert 'data-cwtbl-placeholder' in s
```

Run and verify failure.

- [ ] **Step 2: Implement fixed round metadata and placeholders**

```js
const __cwTblCoppaRounds=[
  {key:'r32',label:'1/16',slots:16},
  {key:'r16',label:'1/8',slots:8},
  {key:'qf',label:'1/4',slots:4},
  {key:'sf',label:'1/2',slots:2},
  {key:'final',label:'Финал',slots:1}
];
function __cwTblRoundMatches(payload,key){const round=(payload?.rounds||[]).find(r=>String(r.key)===key);return Array.isArray(round?.matches)?round.matches:[]}
```

Render `Math.max(meta.slots, actual.length)` cards so provider-supplied extra events are never truncated. Empty indices become premium placeholders with `data-cwtbl-placeholder` and no match click attribute.

- [ ] **Step 3: Implement real match card renderer**

```js
function __cwTblCoppaTeam(t,winner){const local=Number(t?.local_team_id)||0,crest=t?.crest_url?`<img loading="lazy" decoding="async" src="${esc(t.crest_url)}" alt="">`:'<span>⚽</span>';return `<span class="cwtbl-coppa-team${winner?' winner':''}"${local?` data-cwtbl-club="${local}" role="button" tabindex="0"`:''}>${crest}<b>${esc(t?.name||'Участник определяется')}</b></span>`}
function __cwTblCoppaMatch(m){
  if(!m)return `<article class="cwtbl-coppa-match placeholder" data-cwtbl-placeholder><div class="cwtbl-placeholder-line"></div><span>Участники определяются</span></article>`;
  const id=Number(m.external_match_id)||0,live=String(m.status)==='live',finished=String(m.status)==='finished',score=(live||finished)&&m.home_score!=null&&m.away_score!=null?`${Number(m.home_score)}:${Number(m.away_score)}`:'—';
  return `<article class="cwtbl-coppa-match${live?' live':''}${finished?' finished':''}"${id?` data-cwtbl-match="${id}" role="button" tabindex="0"`:''}>${__cwTblCoppaTeam(m.home,m.winner_side==='home')}<div class="cwtbl-coppa-score"><b>${score}</b><small>${live?`LIVE${m.minute!=null?` · ${Number(m.minute)}′`:''}`:finished?'Завершён':m.kickoff_at?fmt(m.kickoff_at):'Время уточняется'}</small></div>${__cwTblCoppaTeam(m.away,m.winner_side==='away')}</article>`;
}
```

- [ ] **Step 4: Implement horizontal bracket**

```js
function __cwTblCoppaHtml(payload){return `<div class="cwtbl-bracket" data-cwtbl-bracket>${__cwTblCoppaRounds.map(meta=>{const actual=__cwTblRoundMatches(payload,meta.key),count=Math.max(meta.slots,actual.length);return `<section class="cwtbl-round" data-cwtbl-round="${meta.key}"><div class="cwtbl-round-title"><b>${meta.label}</b><span>${actual.length?`${actual.length} матч.`:'ожидается'}</span></div><div class="cwtbl-round-list">${Array.from({length:count},(_,i)=>__cwTblCoppaMatch(actual[i]||null)).join('')}</div></section>`}).join('')}</div>`}
```

CSS:

```css
#ciao-miniapp-root .cwtbl-bracket{display:flex;gap:12px;overflow-x:auto;overflow-y:visible;scroll-snap-type:x mandatory;overscroll-behavior-x:contain;margin:0 -14px;padding:2px 14px 18px;scrollbar-width:none}
#ciao-miniapp-root .cwtbl-round{flex:0 0 min(86vw,340px);scroll-snap-align:center;min-width:0}
#ciao-miniapp-root .cwtbl-round-list{display:flex;flex-direction:column;justify-content:space-around;gap:10px;min-height:100%}
#ciao-miniapp-root .cwtbl-coppa-match{position:relative;border:1px solid rgba(var(--cwtbl-rgb),.20);border-radius:17px;background:linear-gradient(180deg,rgba(14,27,24,.96),rgba(7,13,12,.96));padding:10px;box-shadow:0 12px 30px rgba(0,0,0,.22)}
#ciao-miniapp-root .cwtbl-coppa-match::after{content:'';position:absolute;right:-13px;top:50%;width:13px;height:1px;background:rgba(255,255,255,.15)}
#ciao-miniapp-root .cwtbl-round:last-child .cwtbl-coppa-match::after{display:none}
```

Connector lines are decorative only; no canvas/SVG routing is required.

- [ ] **Step 5: Wire Match Center and team-profile click isolation**

```js
main?.querySelectorAll?.('[data-cwtbl-match]').forEach(card=>card.addEventListener('click',ev=>{if(ev.target.closest('[data-cwtbl-club]'))return;const id=Number(card.dataset.cwtblMatch);if(id)openMatchCenter(id,'external')}));
main?.querySelectorAll?.('[data-cwtbl-match]').forEach(card=>card.addEventListener('keydown',ev=>{if((ev.key==='Enter'||ev.key===' ')&&!ev.target.closest('[data-cwtbl-club]')){ev.preventDefault();const id=Number(card.dataset.cwtblMatch);if(id)openMatchCenter(id,'external')}}));
```

Team controls keep the Task 2 handler, call `stopPropagation`, and open only local Ciao profiles.

- [ ] **Step 6: Focus the nearest active round after render**

`__cwTblFocusActiveRound()` chooses in order:

1. round containing a `status==='live'` event;
2. earliest round containing a scheduled future event;
3. latest round containing a finished event;
4. `r32`.

After successful Coppa load:

```js
requestAnimationFrame(()=>main?.querySelector?.(`[data-cwtbl-round="${key}"]`)?.scrollIntoView({behavior:'auto',block:'nearest',inline:'center'}));
```

- [ ] **Step 7: Run contract/syntax checks and commit**

```bash
python work/tournament-tables/frontend/tests/tables-contract.py
# repeat inline node --check command
git add index.html work/tournament-tables/frontend/tests/tables-contract.py
git commit -m "feat: add premium Coppa Italia bracket"
```

---

### Task 4: Add refresh scheduling, return-state polish, and Serie A guards

**Files:**
- Modify: `index.html` tables layer.
- Modify: `work/tournament-tables/frontend/tests/tables-contract.py`

**Interfaces:**
- Produces `__cwTblSchedule`, `__cwTblStopTimer`, external-table refresh isolation, and existing Serie A refresh guard.

- [ ] **Step 1: Add failing assertions**

```python
assert 'function __cwTblSchedule' in s
assert 'function __cwTblStopTimer' in s
assert 'document.hidden' in s
assert "__cwTblCompetition!=='serie_a'" in s
```

- [ ] **Step 2: Implement isolated refresh timer**

```js
function __cwTblStopTimer(){if(__cwTblTimer){clearTimeout(__cwTblTimer);__cwTblTimer=null}}
function __cwTblPollDelay(){if(__cwTblCompetition==='coppa_italia'){const live=(__cwTblPayload?.rounds||[]).some(r=>(r.matches||[]).some(m=>String(m.status)==='live'));return live?15000:300000}return ['ucl','uel','uecl'].includes(__cwTblCompetition)?30000:300000}
function __cwTblSchedule(){__cwTblStopTimer();if(document.hidden||tab!=='seriea'||!['ucl','uel','uecl','coppa_italia'].includes(__cwTblCompetition))return;__cwTblTimer=setTimeout(()=>{if(!document.hidden&&tab==='seriea')__cwTblLoad(__cwTblCompetition,{quiet:true})},__cwTblPollDelay())}
document.addEventListener('visibilitychange',()=>{if(document.hidden)__cwTblStopTimer();else if(tab==='seriea')__cwTblSchedule()});
```

Quiet refresh must keep the current table/bracket on screen while the request is in flight.

- [ ] **Step 3: Guard legacy Serie A network refresh outside the Serie A child screen**

If `__cw11RefreshSerieA` exists at this late layer:

```js
if(typeof __cw11RefreshSerieA==='function'){
  const __cwTblLegacySerieRefresh=__cw11RefreshSerieA;
  __cw11RefreshSerieA=async function(...args){if(tab==='seriea'&&__cwTblCompetition&&__cwTblCompetition!=='serie_a')return;return await __cwTblLegacySerieRefresh(...args)};
}
```

If `__cw2017PatchSerieA` exists, apply the same guard before invoking the old patcher. This prevents unrelated Serie A DOM churn while a UEFA/Coppa table is visible.

- [ ] **Step 4: Preserve tables sub-screen when returning from club profile or Match Center**

The existing `openClubProfile`/`openMatchCenter` systems already preserve `tab`. Add tables state to the v32 match-return snapshot by wrapping `__cw32CaptureReturn` if it is assignable, or store `__cwTblCompetition` independently in a module variable that is never reset on deep navigation. `data-cwtbl-back` is the only action that intentionally clears the tournament selection.

Verify manually:

```text
UCL -> Inter profile -> back -> UCL same table
Coppa -> match -> Match Center -> back -> Coppa same bracket/round scroll
```

- [ ] **Step 5: Ensure theme cleanup on leaving Tables**

Wrap `render` once at the end of the layer:

```js
const __cwTblRenderBase=render;
render=function(){const r=__cwTblRenderBase();const theme=tab==='seriea'&&__cwTblCompetition?__cwTblMeta[__cwTblCompetition]?.theme:'';if(theme)root.setAttribute('data-cwtbl-theme',theme);else root.removeAttribute('data-cwtbl-theme');if(tab!=='seriea')__cwTblStopTimer();return r};
```

Do not remove existing `data-cwmt-screen-theme`, `data-cwpred-screen-theme`, or Rating theme classes; each subsystem manages its own attribute.

- [ ] **Step 6: Run regressions and commit**

```bash
python work/tournament-tables/frontend/tests/tables-contract.py
# inline node --check
```

Static regression assertions must still include:

```python
for marker in ['ciao-v29-native-score-picker-20260908','ciao-v32-live-poll-5s-20260908','ciao-prod-multitournament-matches-20260907','ciao-prod-multitournament-predictions-20260907','ciao-premium-italy-loading-system-20260909']:
    assert marker in s
```

Commit:

```bash
git add index.html work/tournament-tables/frontend/tests/tables-contract.py
git commit -m "fix: isolate tournament table refresh state"
```

---

### Task 5: Visual smoke, production promotion, and index-only verification

**Files:**
- Modify only if smoke finds defects: feature-branch `index.html`.
- Production write: root `index.html` only.

**Interfaces:**
- Consumes deployed `ciao-tournament-tables-v1` from the backend plan.
- Produces final production Pages build with no repository-tree extras.

- [ ] **Step 1: Run complete static/syntax verification**

```bash
python work/tournament-tables/frontend/tests/tables-contract.py
python - <<'PY'
from pathlib import Path
import re, subprocess, tempfile
s=Path('index.html').read_text()
scripts=re.findall(r'<script([^>]*)>(.*?)</script>',s,re.S|re.I)
checked=0
for i,(attrs,js) in enumerate(scripts):
    a=attrs.lower()
    if 'src=' in a or ('type=' in a and 'javascript' not in a and 'module' not in a) or not js.strip(): continue
    p=Path(tempfile.gettempdir())/f'ciao-final-{i}.js';p.write_text(js);subprocess.run(['node','--check',str(p)],check=True);checked+=1
print('checked',checked,'inline scripts')
PY
```

Expected: PASS.

- [ ] **Step 2: Browser/Mini App visual smoke at narrow widths**

Check at approximately 360 px and 390–430 px widths:

```text
Tables hub: five cards, no clipping
Serie A: unchanged rows/live zones
UCL/UEL/UECL: 36 rows, readable names, no page horizontal scroll, zones visible but subtle
Italian UEFA row: opens profile; foreign row: inert
Coppa: bracket scrolls horizontally inside its container only; snap works
Coppa actual match: opens full external Match Center
Coppa placeholder: inert
Back from profile/Match Center: selected tournament retained
Loading: compact Italian premium bar
```

- [ ] **Step 3: Fix only defects found by smoke and rerun all checks**

Any fix must remain inside the `ciao-v34-tournament-tables-20260909` layer unless an existing global bug is proven to be the cause. Do not refactor unrelated code.

- [ ] **Step 4: Promote only `index.html` to `main`**

Do not merge the implementation branch wholesale. Update `main` with the verified feature-branch `index.html` content only, preserving the rest of the `main` tree as empty.

Commit message:

```text
feat: add tournament tables and Coppa bracket
```

- [ ] **Step 5: Verify production tree invariant**

Fetch recursive tree for the new `main` SHA and assert exactly one path:

```text
index.html
```

No `docs/`, `work/`, `.github/`, tests, migrations, or backend source may exist on production `main`.

- [ ] **Step 6: Verify GitHub Pages deployment**

Wait for the Pages workflow run whose `head_sha` equals the final `main` SHA and require:

```text
status = completed
conclusion = success
```

- [ ] **Step 7: Final production smoke**

Open the production Mini App/Page and repeat one representative flow per subsystem:

```text
UCL full table -> Italian club -> back
Europa full table scroll
Conference full table scroll
Coppa bracket -> real match -> Match Center -> back
Serie A table live renderer
Predictions score picker cw29
Matches external tournament card
Rating competition selector
```

Only after these checks report the feature complete.
