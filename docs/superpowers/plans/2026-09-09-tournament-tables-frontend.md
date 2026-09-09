# Tournament Tables Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` task-by-task. Use RED → GREEN → verification and do not promote to `main` until backend smoke and mobile visual smoke pass.

**Goal:** Turn the existing `Таблицы` tab into a five-tournament premium hub with the existing Serie A table, full 36-club UEFA tables, and a swipeable complete Coppa Italia bracket.

**Architecture:** Add one late compatibility layer to the current single-file `index.html`. Capture the latest existing `serieA`, `bind`, `render`, and Serie A refresh behavior, then route only `tab==='seriea'` through a new tables controller. External screens read only `ciao-tournament-tables-v1`. Existing deep navigation remains authoritative: local clubs use `openClubProfile(local_team_id)` and Coppa actual matches use `openMatchCenter(external_match_id,'external')`.

**Tech stack:** existing vanilla HTML/CSS/JS, current premium loading system, existing Ciao club-profile and Match Center navigation.

**Spec:** `docs/superpowers/specs/2026-09-09-tournament-tables-design.md`

## Non-negotiable contracts

- Final production `main` contains **only `index.html`**.
- Preserve `cw29`, Predictions, Matches, Rating, Match Center APIs, and the 5-second live scheduler.
- Hub has exactly: Serie A, Coppa Italia, Champions League, Europa League, Conference League.
- UEFA renders 36 rows, no page-level horizontal scroll.
- Only numeric `local_team_id` is interactive as a club profile.
- Every actual Coppa event with numeric `external_match_id` opens full existing external Match Center.
- Coppa placeholder slots are inert.
- Shared Italian premium loading animation is reused.
- Existing Serie A renderer/live behavior remains the source of truth for Serie A.

---

## Task 1 — Controller shell and five-tournament hub

**Files**
- Modify on feature branch: `index.html`
- Create on feature branch only: `work/tournament-tables/frontend/tests/tables-contract.py`

- [ ] **RED:** static contract requires new marker/API and five hub competition IDs while preserving critical production markers:

```python
from pathlib import Path
s=Path('index.html').read_text()
assert 'ciao-v34-tournament-tables-20260909' in s
assert "const __CWTBL_API='https://dkefzepiiudehhzbbrjn.supabase.co/functions/v1/ciao-tournament-tables-v1'" in s
for key in ['serie_a','coppa_italia','ucl','uel','uecl']:
    assert f'data-cwtbl-competition="{key}"' in s
for marker in ['ciao-v29-native-score-picker-20260908','ciao-v32-live-poll-5s-20260908','ciao-prod-multitournament-matches-20260907','ciao-prod-multitournament-predictions-20260907','ciao-premium-italy-loading-system-20260909']:
    assert marker in s
assert '__CW2014_LIVE_MS=5000' in s
```

Run and expect FAIL on the new tables marker.

- [ ] **GREEN:** append one delimited late layer:

```js
/* ===== ciao-v34-tournament-tables-20260909 ===== */
const __CWTBL_API='https://dkefzepiiudehhzbbrjn.supabase.co/functions/v1/ciao-tournament-tables-v1';
const __cwTblLegacySerieA=serieA;
const __cwTblLegacyBind=bind;
let __cwTblCompetition='';
let __cwTblPayload=null;
let __cwTblLoading=false;
let __cwTblError='';
let __cwTblRequestVersion=0;
let __cwTblTimer=null;
let __cwTblBracketScrollLeft=0;
const __cwTblMeta={
  serie_a:{title:'Серия А',theme:'serie-a',wide:true},
  coppa_italia:{title:'Кубок Италии',theme:'coppa'},
  ucl:{title:'Лига Чемпионов',theme:'champions'},
  uel:{title:'Лига Европы',theme:'europa'},
  uecl:{title:'Лига Конференций',theme:'conference'}
};
```

Implement:

```text
__cwTblHubHtml()
__cwTblCover(key)
__cwTblScreenHtml()
__cwTblSelect(key)
```

`serieA=function(){ return __cwTblScreenHtml(); }`.

Hub card layout follows existing Predictions/Matches family but uses `cwtbl-*` classes so tables styling cannot leak into those subsystems.

- [ ] Override `bind` by calling captured legacy binder first, then:
  - `[data-cwtbl-competition]` → `__cwTblSelect`;
  - `[data-cwtbl-back]` → save/clear state, stop timer, return to tables hub.

- [ ] Add tournament theme variables:

```css
[data-cwtbl-theme="serie-a"]    {--cwtbl-a:#3150ff;--cwtbl-b:#0b2f88;--cwtbl-rgb:49,80,255}
[data-cwtbl-theme="champions"]  {--cwtbl-a:#5367e6;--cwtbl-b:#49318f;--cwtbl-rgb:83,103,230}
[data-cwtbl-theme="europa"]     {--cwtbl-a:#e66a13;--cwtbl-b:#7a2c05;--cwtbl-rgb:230,106,19}
[data-cwtbl-theme="conference"] {--cwtbl-a:#28a968;--cwtbl-b:#0b3b28;--cwtbl-rgb:40,169,104}
[data-cwtbl-theme="coppa"]      {--cwtbl-a:#159457;--cwtbl-b:#9f2435;--cwtbl-rgb:21,148,87}
```

Use dark gradients/radial light only; do not embed tournament artwork.

- [ ] Verify contract + every inline script with `node --check`.

- [ ] Commit:

```bash
git add index.html work/tournament-tables/frontend/tests/tables-contract.py
git commit -m "feat: add tournament tables hub"
```

---

## Task 2 — Authenticated loading and full UEFA tables

**Files**
- Modify: `index.html` inside the v34 layer
- Modify: `work/tournament-tables/frontend/tests/tables-contract.py`

- [ ] **RED:** require strings/classes for `action:'standings'`, all three zone classes, `data-cwtbl-club`, `rows.length!==36`, retry state, and `cw-it-loading`.

- [ ] Implement authenticated fetch:

```js
async function __cwTblApi(action,competition){
  const r=await fetch(__CWTBL_API,{
    method:'POST',
    headers:{'content-type':'application/json','x-telegram-init-data':initData},
    body:JSON.stringify({action,competition})
  });
  const j=await r.json().catch(()=>({}));
  if(!r.ok||!j?.ok){const e=new Error(j?.error||'Не удалось загрузить данные турнира');e.status=r.status;e.payload=j;throw e}
  return j;
}
```

- [ ] Implement `__cwTblLoad(key,{quiet=false}={})` with request-version guard. Action is `bracket` only for Coppa and `standings` for UEFA. A stale/outdated response must not replace a later selection.

- [ ] Implement external screen state in this order:
  1. themed cover/back;
  2. subtle stale badge when backend returns `stale:true` or an in-place quiet refresh failed;
  3. compact `<div class="cw-it-loading">…</div>` when no payload exists yet;
  4. retry button when no usable payload exists;
  5. current usable table/bracket.

Do not blank existing content during quiet refresh.

- [ ] Implement canonical UEFA row renderer using backend fields only:

```text
# | Команда | И | РМ | О
secondary team line: В-Н-П · goals_for:goals_against
```

A row is a `<button>` only if `Number(local_team_id)>0`; otherwise it is a non-interactive `<div>`. Never infer clickability from country text/name in the browser.

- [ ] Render exactly 36 rows; if payload is not 36, show `Таблица временно неполная` instead of presenting a misleading partial table.

- [ ] Add compact legend and subtle zones:

```text
1–8   direct
9–24  playoff
25–36 eliminated
```

Use thin left accents + very low-opacity tint, not large blocks of color.

- [ ] Mobile CSS uses:

```css
.cwtbl-head,.cwtbl-row{
  display:grid;
  grid-template-columns:28px minmax(0,1fr) 28px 38px 32px;
  align-items:center;
  gap:6px;
}
.cwtbl-table{width:100%;min-width:0;overflow:hidden}
.cwtbl-team{min-width:0}
.cwtbl-team b{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
```

No parent/page horizontal overflow.

- [ ] Bind `[data-cwtbl-club]` to `openClubProfile(id)` with `preventDefault()` and `stopPropagation()`. Foreign rows have no click handler, button semantics, tabindex, or pointer styling.

- [ ] Verify contract + inline syntax; commit:

```bash
git add index.html work/tournament-tables/frontend/tests/tables-contract.py
git commit -m "feat: add premium UEFA tables"
```

---

## Task 3 — Complete Coppa Italia swipe bracket

**Files**
- Modify: `index.html`
- Modify: `work/tournament-tables/frontend/tests/tables-contract.py`

- [ ] **RED:** require round keys `r32/r16/qf/sf/final`, `scroll-snap-type:x mandatory`, `data-cwtbl-match`, `data-cwtbl-placeholder`, and `openMatchCenter(id,'external')`.

- [ ] Define display metadata:

```js
const __cwTblCoppaRounds=[
  {key:'r32',label:'1/16',slots:16},
  {key:'r16',label:'1/8',slots:8},
  {key:'qf',label:'1/4',slots:4},
  {key:'sf',label:'1/2',slots:2},
  {key:'final',label:'Финал',slots:1}
];
```

For each round, render `Math.max(meta.slots, actualMatches.length)`. This preserves all actual provider events (including possible extra legs) while still showing premium unknown-participant placeholders for future slots.

- [ ] Actual match card fields:
  - home/away crest + name;
  - live/finished score;
  - `LIVE · minute`, `Завершён`, or kickoff time;
  - winner emphasis from `winner_side`;
  - `data-cwtbl-match="external_match_id"` only when numeric ID exists.

Unknown slots use `data-cwtbl-placeholder`, no role/tabindex/click handler.

- [ ] Team name/crest inside a Coppa match gets `data-cwtbl-club` only when local ID exists. The club handler stops propagation so it never simultaneously opens the match.

- [ ] Bind actual card click/Enter/Space to:

```js
openMatchCenter(id,'external')
```

- [ ] Bracket CSS:

```css
.cwtbl-bracket{
  display:flex;
  gap:12px;
  overflow-x:auto;
  overflow-y:visible;
  scroll-snap-type:x mandatory;
  overscroll-behavior-x:contain;
  scrollbar-width:none;
}
.cwtbl-round{flex:0 0 min(86vw,340px);scroll-snap-align:center;min-width:0}
```

Global app shell must not scroll horizontally. Connector lines are restrained CSS decoration only; no canvas/SVG routing dependency.

- [ ] Implement `__cwTblActiveRoundKey(payload)` choosing:
  1. round with live event;
  2. earliest round with scheduled future event;
  3. latest round with finished event;
  4. `r32`.

On first successful Coppa render when there is no saved horizontal position, center that round.

- [ ] Verify and commit:

```bash
git add index.html work/tournament-tables/frontend/tests/tables-contract.py
git commit -m "feat: add premium Coppa Italia bracket"
```

---

## Task 4 — Refresh isolation and exact deep-return state

**Files**
- Modify: `index.html`
- Modify: `work/tournament-tables/frontend/tests/tables-contract.py`

- [ ] **RED:** require `__cwTblSchedule`, `__cwTblStopTimer`, hidden-tab guard, non-Serie-A refresh guard, and `__cwTblBracketScrollLeft` capture/restore contract.

- [ ] Implement independent external tables refresh:

```js
function __cwTblStopTimer(){if(__cwTblTimer){clearTimeout(__cwTblTimer);__cwTblTimer=null}}
function __cwTblPollDelay(){
  if(__cwTblCompetition==='coppa_italia'){
    const live=(__cwTblPayload?.rounds||[]).some(r=>(r.matches||[]).some(m=>String(m.status)==='live'));
    return live?15000:300000;
  }
  return ['ucl','uel','uecl'].includes(__cwTblCompetition)?30000:300000;
}
function __cwTblSchedule(){
  __cwTblStopTimer();
  if(document.hidden||tab!=='seriea'||!['ucl','uel','uecl','coppa_italia'].includes(__cwTblCompetition))return;
  __cwTblTimer=setTimeout(()=>{if(!document.hidden&&tab==='seriea')__cwTblLoad(__cwTblCompetition,{quiet:true})},__cwTblPollDelay());
}
```

Visibility change stops/resumes only this timer.

- [ ] Guard legacy Serie A refresh/patch functions whenever:

```js
tab==='seriea' && __cwTblCompetition && __cwTblCompetition!=='serie_a'
```

This prevents a live Serie A update from replacing/patching UEFA or Coppa DOM.

- [ ] Preserve tables selection automatically because `__cwTblCompetition` is module state and is cleared only by `[data-cwtbl-back]`.

- [ ] Preserve **Coppa horizontal position**, not just page scroll:
  - bracket `scroll` listener stores `__cwTblBracketScrollLeft = bracket.scrollLeft`;
  - immediately before local-club or Coppa-match deep navigation, capture the current bracket `scrollLeft`;
  - after returning and rendering Coppa, `requestAnimationFrame` restores `bracket.scrollLeft` when saved value is >0;
  - only if no saved value exists should `__cwTblActiveRoundKey` auto-center a stage.

This explicitly supports:

```text
Coppa stage -> Match Center -> back -> same horizontal bracket position
Coppa stage -> Italian club profile -> back -> same horizontal bracket position
```

- [ ] Existing `openClubProfile` already stores `tab`/vertical scroll. Existing v32 `openMatchCenter(id,'external')` already restores external Match Center source and page return state. Do not replace those systems; add only bracket-local scroll restoration around them.

- [ ] Wrap final `render` once to apply/remove only `data-cwtbl-theme` and stop the tables timer when leaving `tab==='seriea'`. Do not touch `data-cwmt-screen-theme`, `data-cwpred-screen-theme`, or Rating classes.

- [ ] Regression assertions preserve:

```text
ciao-v29-native-score-picker-20260908
ciao-v32-live-poll-5s-20260908
ciao-prod-multitournament-matches-20260907
ciao-prod-multitournament-predictions-20260907
ciao-premium-italy-loading-system-20260909
__CW2014_LIVE_MS=5000
```

- [ ] Verify inline `node --check` and commit:

```bash
git add index.html work/tournament-tables/frontend/tests/tables-contract.py
git commit -m "fix: isolate tournament table refresh state"
```

---

## Task 5 — Visual smoke and production promotion

**Files**
- Fix defects only in feature-branch `index.html`.
- Production write: root `index.html` only.

- [ ] Run complete static contract and inline JS syntax checks.

- [ ] Smoke at roughly 360 px and 390–430 px widths:

```text
Hub: five premium cards, no clipping
Serie A: current renderer/live zones unchanged
UCL/UEL/UECL: 36 readable rows, subtle zones, no page horizontal scroll
Italian UEFA row: profile opens; foreign row: inert
Coppa: horizontal bracket only, snap works, current/nearest stage initial focus works
Coppa actual match: full external Match Center opens
Coppa placeholder: inert
Coppa local club: profile opens without also opening match
Back from club/Match Center: same selected competition; Coppa restores horizontal position
Loading/error/stale states remain premium and usable
```

- [ ] If defects are found, fix only inside the v34 tables layer unless an existing global defect is proven causal; rerun all checks after every fix batch.

- [ ] Promote **only verified `index.html`** to `main`. Do not merge the feature/design branch wholesale.

Production commit message:

```text
feat: add tournament tables and Coppa bracket
```

- [ ] Fetch recursive `main` tree and require exactly one path:

```text
index.html
```

No `docs/`, `work/`, tests, migrations, backend files, or workflows may remain on production `main`.

- [ ] Wait for GitHub Pages run whose `head_sha` equals final `main` SHA and require `completed/success`.

- [ ] Final production smoke:

```text
UCL -> Italian club -> back
UEL full table scroll
UECL full table scroll
Coppa -> real match -> Match Center -> back to same bracket position
Serie A table live update
Predictions cw29 score picker
Matches external tournament navigation
Rating competition selector
```

Only after these checks report completion.
