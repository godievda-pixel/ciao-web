# External Match Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the existing full BSD-powered Match Center to UCL, UEL, UECL and Coppa Italia, with tournament-specific themes, while preserving Serie A Match Center and prediction editing.

**Architecture:** Keep one Match Center UI and one backend family, but make identity explicit with `source: 'serie_a' | 'external'`. Normalize `cp_matches` and `cp_external_matches` into one response shape, use a separate external cache table, and propagate `matchViewSource` through navigation, polling, lazy sections and session restore.

**Tech Stack:** Supabase Postgres, Supabase Edge Functions (Deno + `@supabase/supabase-js`), BSD Sports API, single-file GitHub Pages frontend (`index.html`), vanilla JavaScript/CSS, temporary GitHub Actions/source-contract checks.

**Spec:** `docs/superpowers/specs/2026-09-08-external-match-center-design.md`

## Global Constraints

- Production repository: `godievda-pixel/ciao-web`, branch `main`.
- Never touch `godievda-pixel/ciao-pronostici`.
- After user acceptance, production tree returns to root `index.html` only; spec/plan/test/workflow artifacts are temporary.
- Serie A Match Center remains functionally unchanged except for explicit source plumbing.
- `cw29` picker and prediction autosave remain unchanged.
- Club-profile navigation remains disabled inside Predictions.
- External Match Center never renders “Контекст Серии А”.
- External identity is always `(source, match_id)`, never numeric `match_id` alone.
- Optional BSD sections fail locally without replacing the whole Match Center.
- Rating work is out of scope for this feature.

---

## File / Service Map

- Database: create `public.cp_external_match_center_cache`.
- Edge Function: modify `ciao-match-summary-fast-v2`.
- Edge Function: modify `ciao-match-center-fast-v3`.
- Frontend: modify `index.html` only.
- Temporary test/workflow files may exist during implementation and must be removed after acceptance.

---

### Task 1: External Cache Table

**Files / Services:** Supabase schema, project `dkefzepiiudehhzbbrjn`.

**Interfaces:** consumes `cp_external_matches(id, provider_event_id)`; produces source-isolated cache keyed by `external_match_id`.

- [ ] **Step 1: RED schema contract**

```sql
select to_regclass('public.cp_external_match_center_cache') as cache_table;
```

Expected before migration: `null`.

- [ ] **Step 2: Apply migration**

```sql
create table public.cp_external_match_center_cache (
  external_match_id bigint primary key
    references public.cp_external_matches(id) on delete cascade,
  provider_event_id bigint not null,
  status text null,
  payload jsonb not null default '{}'::jsonb,
  fetched_at timestamptz not null default now()
);

alter table public.cp_external_match_center_cache enable row level security;
```

No anon/authenticated policies: Edge Functions use service role.

- [ ] **Step 3: GREEN schema contract**

```sql
select to_regclass('public.cp_external_match_center_cache') as cache_table,
       c.relrowsecurity as rls_enabled
from pg_class c
where c.oid='public.cp_external_match_center_cache'::regclass;
```

Expected: table exists, `rls_enabled=true`.

- [ ] **Step 4: Verify FK isolation**

```sql
select conname, pg_get_constraintdef(oid) as definition
from pg_constraint
where conrelid='public.cp_external_match_center_cache'::regclass;
```

Expected FK references `cp_external_matches(id)`, not `cp_matches(id)`.

---

### Task 2: Source-Aware Summary API

**Files / Services:** deployed `ciao-match-summary-fast-v2/index.ts`.

**Interfaces:** request `{ source?: 'serie_a'|'external', match_id:number }`; response `{ ok, source, match, competition, stage, prediction_split, status, summary_only, recommended_poll_ms }`.

- [ ] **Step 1: RED source contract**

Inspect current source and prove:

```text
getMatch() reads only cp_matches
getSplit() reads only cp_predictions
request body has no source branch
```

Capture a real external match:

```sql
select id,competition,provider_event_id
from cp_external_matches
order by id
limit 1;
```

- [ ] **Step 2: Add source parser**

```ts
function sourceOf(body:any){
  return String(body?.source??'serie_a')==='external' ? 'external' : 'serie_a';
}
```

- [ ] **Step 3: Normalize internal and external matches**

Internal normalized fields:

```ts
{
  id, source:'serie_a', competition:'serie_a',
  provider_event_id:bsd_event_id, bsd_event_id,
  kickoff_at, home_score, away_score, is_finished,
  live_status, live_elapsed, round,
  home:{id,bsd_team_id,name,short_name,custom_emoji_id,crest_url:null,country_code:null},
  away:{id,bsd_team_id,name,short_name,custom_emoji_id,crest_url:null,country_code:null},
  prediction
}
```

External normalized fields:

```ts
{
  id, source:'external', competition,
  provider_event_id, bsd_event_id:provider_event_id,
  stage_key, stage_label, stage_order, round_number,
  kickoff_at, home_score, away_score,
  is_finished:status==='finished', live_status:status, live_elapsed:minute,
  home:{id:null,bsd_team_id:home_bsd_team_id,name:home_name,short_name:null,custom_emoji_id:null,crest_url:home_crest_url,country_code:home_country_code},
  away:{id:null,bsd_team_id:away_bsd_team_id,name:away_name,short_name:null,custom_emoji_id:null,crest_url:away_crest_url,country_code:away_country_code},
  prediction
}
```

External user prediction query:

```ts
db.from('cp_external_predictions')
  .select('home_score,away_score,points,updated_at')
  .eq('user_id',userId)
  .eq('external_match_id',matchId)
  .maybeSingle()
```

- [ ] **Step 4: Make prediction split source-aware**

For external:

```ts
db.from('cp_external_predictions')
  .select('home_score,away_score')
  .eq('external_match_id',matchId)
```

Use source-qualified cache key:

```ts
const splitKey=`${source}:${matchId}`;
```

- [ ] **Step 5: Normalize external status**

```ts
function externalStatus(s:string){
  const x=String(s||'').toLowerCase();
  if(['live','halftime','extra_time','penalties'].includes(x))return 'live';
  if(x==='finished')return 'finished';
  return 'upcoming';
}
```

Keep original DB status in `match.live_status` for postponed/cancelled presentation.

- [ ] **Step 6: Return explicit metadata**

```ts
{
  ok:true,
  source,
  match,
  competition:match.competition,
  stage:source==='external'?{
    key:match.stage_key,
    label:match.stage_label,
    order:match.stage_order,
    round_number:match.round_number
  }:null,
  prediction_split,
  status,
  summary_only:true,
  recommended_poll_ms
}
```

- [ ] **Step 7: GREEN source contract and deploy**

Verify source contains `cp_external_matches`, separate external prediction queries, source-qualified split key, and explicit competition/stage response. Deploy same slug with `verify_jwt=false` because custom Telegram auth remains in the function.

---

### Task 3: Source-Aware Full/Lazy API

**Files / Services:** deployed `ciao-match-center-fast-v3/index.ts`.

**Interfaces:** request `{ source?:'serie_a'|'external', match_id:number, sections?:string[], include_split?:boolean }`; response shares Task 2 normalized match metadata plus BSD lazy sections.

- [ ] **Step 1: RED source contract**

Prove current implementation is internal-only:

```text
loadMatch() only cp_matches
predictionSplit() only cp_predictions
cache helpers hardcoded to cp_match_center_cache + match_id
fetchOverviewMeta() assumes match.bsd_event_id
```

- [ ] **Step 2: Reuse Task 2 normalized match shape**

Do not create a second external frontend shape.

- [ ] **Step 3: Add cache descriptor**

```ts
function cacheSpec(source:string){
  return source==='external'
    ? {table:'cp_external_match_center_cache',key:'external_match_id',event:'provider_event_id'}
    : {table:'cp_match_center_cache',key:'match_id',event:'bsd_event_id'};
}
```

Update `ensureCacheRow`, `readCache`, `claimRefresh`, `waitForRefresh` and final `upsert` to receive source.

- [ ] **Step 4: Make all in-memory keys collision-safe**

```ts
`${match.source}:${match.id}:${[...sections].sort().join(',')}`
```

Prediction split cache keys also include source.

- [ ] **Step 5: Make BSD event access source-neutral**

```ts
const eventId=Number(match.provider_event_id??match.bsd_event_id);
```

`fetchOverviewMeta()` uses normalized `match.home.bsd_team_id` and `match.away.bsd_team_id`.

- [ ] **Step 6: Preserve lazy sections and graceful errors**

Reuse existing section set:

```text
detail, stats, incidents, lineups, player_stats, overview_meta
```

A failed BSD section updates only its error entry and keeps cached successful sections.

- [ ] **Step 7: Return source/competition/stage**

Full response includes `source`, `competition`, `stage` plus existing coverage/data/error fields.

- [ ] **Step 8: GREEN contract and deploy**

Verify both source loaders exist; external cache is used only for external source; source participates in flight/split/cache identity; BSD routes use normalized provider ID; no external-to-Serie-A fallback exists. Deploy same slug, keeping custom Telegram auth.

---

### Task 4: Backend Data and Collision Smoke

**Files / Services:** read-only SQL + deployed function source.

- [ ] **Step 1: Provider coverage**

```sql
select competition,
       count(*) as matches,
       count(provider_event_id) as with_provider_event,
       count(home_bsd_team_id) as with_home_bsd,
       count(away_bsd_team_id) as with_away_bsd
from cp_external_matches
group by competition
order by competition;
```

Expected current coverage:

```text
coppa_italia 12/12/12/12
ucl          32/32/32/32
uecl          8/8/8/8
uel          16/16/16/16
```

- [ ] **Step 2: Find an overlapping numeric ID**

```sql
select e.id,e.competition,e.home_name as external_home,e.away_name as external_away,m.id as serie_a_id
from cp_external_matches e
join cp_matches m on m.id=e.id
order by e.id
limit 1;
```

This ID must resolve differently for `source='external'` vs `source='serie_a'`.

- [ ] **Step 3: Verify prediction-table isolation with an executable CTE**

```sql
with chosen as (
  select external_match_id
  from cp_external_predictions
  group by external_match_id
  order by count(*) desc, external_match_id
  limit 1
)
select chosen.external_match_id,
       (select count(*) from cp_external_predictions ep where ep.external_match_id=chosen.external_match_id) as external_predictions,
       (select count(*) from cp_predictions p where p.match_id=chosen.external_match_id) as serie_a_predictions_same_numeric_id
from chosen;
```

The counts are independent; source decides which table is used.

- [ ] **Step 4: Verify physical cache isolation**

For the collision ID, query `cp_match_center_cache` and `cp_external_match_center_cache` separately. No code path may substitute one table for the other.

---

### Task 5: Frontend Source Plumbing

**Files:** modify `index.html`; temporary one-time source-contract workflow/script.

**Interfaces:** produces `matchViewSource` and source-aware summary/full API helpers; legacy callers default to Serie A.

- [ ] **Step 1: RED frontend contract**

Fail unless active source contains:

```text
matchViewSource
source-aware openMatchCenter
summary request source
lazy request source
session snapshot source
```

- [ ] **Step 2: Add state**

```js
let matchViewSource='serie_a';
```

- [ ] **Step 3: Make API helpers source-aware**

```js
const __cw9FastMatchApi=(id,sections=[],source=matchViewSource)=>
  __cw9Post(__CW9_MATCH_API,{source,match_id:Number(id),sections,include_split:false},'Не удалось загрузить Матч-центр');

const __cw9SummaryApi=(id,source=matchViewSource)=>
  __cw9Post(__CW9_SUMMARY_API,{source,match_id:Number(id)},'Не удалось загрузить матч');
```

All refresh/lazy calls use the current source.

- [ ] **Step 4: Update open/close**

```js
openMatchCenter=async function(id,source='serie_a'){
  matchViewSource=source==='external'?'external':'serie_a';
  matchViewId=Number(id);
  // existing loading/render flow
}
```

Reset source only after return state has been captured.

- [ ] **Step 5: Persist/restore source**

Add `matchViewSource` to session snapshots and to any match↔club return snapshots that already carry `matchViewId` and `matchCenterTab`.

- [ ] **Step 6: GREEN and syntax check**

Extract inline scripts and run:

```bash
node --check /tmp/ciao-inline.js
```

Expected exit 0; source-plumbing markers must exist in the active layer.

---

### Task 6: Entry Points From Matches and Predictions

**Files:** modify `index.html`.

**Interfaces:** external cards call `openMatchCenter(externalId,'external')`; prediction controls never trigger Match Center.

- [ ] **Step 1: RED card contract**

Fail until external cards expose a stable external ID/source and have no Match Center binding.

- [ ] **Step 2: Add external locator attributes**

External cards use data equivalent to:

```html
data-external-match-id="42" data-match-source="external"
```

- [ ] **Step 3: Bind Matches cards**

Free-card tap calls:

```js
openMatchCenter(Number(card.dataset.externalMatchId),'external')
```

Tournament/stage controls are excluded.

- [ ] **Step 4: Bind Predictions cards with hard guard**

Ignore events originating from:

```js
'.cw29-score-pick, #cw29-score-picker, button, [data-cwpred-action], [data-cwpred-pick]'
```

Only free card space opens external Match Center.

- [ ] **Step 5: `cw29` regression contract**

Verify one canonical `cw29` picker remains, no `cw28` classes return, picker selection still schedules existing autosave, and external-card guard contains `.cw29-score-pick`.

- [ ] **Step 6: Syntax check**

Run inline `node --check`, expected exit 0.

---

### Task 7: External Presentation and Tournament Themes

**Files:** modify `index.html`.

**Interfaces:** consumes normalized `source`, `competition`, `stage`, `crest_url`.

- [ ] **Step 1: RED presentation contract**

Fail until active source has theme mapping for `ucl`, `uel`, `uecl`, `coppa_italia` and a source guard around Serie A context.

- [ ] **Step 2: Make logo renderer source-neutral**

Priority:

```js
if(t?.crest_url) return external crest image;
if(t?.custom_emoji_id) return existing Telegram emoji image;
return football fallback;
```

External crests use fixed dimensions and `object-fit:contain`.

- [ ] **Step 3: Add tournament labels and stage hero**

```js
const labels={
  ucl:'Лига чемпионов',
  uel:'Лига Европы',
  uecl:'Лига конференций',
  coppa_italia:'Кубок Италии'
};
```

External subtitle:

```js
`${labels[d.competition]||'Матч'}${d.stage?.label?' · '+d.stage.label:''}`
```

Serie A keeps existing round/date presentation.

- [ ] **Step 4: Hard-disable Serie A context for external source**

At the start of the active context renderer:

```js
if(String(d?.source||d?.match?.source||'serie_a')!=='serie_a')return '';
```

No CSS-only hiding and no Serie A context lookups for external render.

- [ ] **Step 5: Add theme classes**

```text
mc-theme-ucl   → midnight/navy + violet/electric-blue
mc-theme-uel   → graphite + orange
mc-theme-uecl  → graphite + saturated green
mc-theme-coppa → deep navy + restrained green/red
```

Only hero, badges, active tabs, borders and subtle glow vary; layout/tabs remain shared.

- [ ] **Step 6: Keep shared tabs**

Reuse existing Overview, Stats, Events, Lineups and Players renderers against normalized payloads.

- [ ] **Step 7: GREEN + syntax**

Verify all theme classes, external stage hero, source guard, crest priority and `node --check` success.

---

### Task 8: Production Verification and Rollout

**Files / Services:** `index.html`, both deployed Match Center functions, GitHub Pages.

- [ ] **Step 1: Preserve a stable pre-frontend backup point**

Create a backup branch from the exact `main` commit immediately before the production frontend patch.

- [ ] **Step 2: Run full static contract**

Required assertions:

```text
matchViewSource exists
legacy callers default to serie_a
external cards open source external
cw29 picker unchanged
no cw28 layer
external context guard present
all four theme mappings present
```

- [ ] **Step 3: Run inline JS syntax verification**

`node --check` must exit 0.

- [ ] **Step 4: Re-read active Edge Function versions**

Confirm external loaders, external prediction tables, external cache table and source-qualified keys are present.

- [ ] **Step 5: Re-check database cache/RLS/FK**

Confirm external cache exists, RLS enabled, FK points to `cp_external_matches`.

- [ ] **Step 6: Commit frontend**

```text
feat: add external tournament match centers
```

- [ ] **Step 7: Verify GitHub Pages deploy on that SHA**

Build and deploy jobs must both succeed.

- [ ] **Step 8: Telegram Mini App visual smoke**

Validate UCL plus at least one of UEL/UECL/Coppa; confirm no Serie A context externally; confirm Serie A Match Center still works; confirm score picker/autosave; confirm Back restores tournament/stage/scroll.

- [ ] **Step 9: Cleanup after user acceptance**

Delete temporary workflows/tests/spec/plan artifacts and verify final production tree again contains only root `index.html`.

---

## Self-Review Checklist

- Spec coverage: source identity, separate cache, normalized match data, external predictions/split, entry points, picker guard, themes, context removal, navigation restore, lazy/live refresh, graceful degradation and cleanup each map to a task.
- No execution step depends on an unresolved placeholder value; SQL smoke queries select their own real IDs.
- Type consistency: every layer uses `source:'serie_a'|'external'`; frontend state is `matchViewSource`; external primary key remains numeric `matchViewId`; normalized provider event is `provider_event_id` with `bsd_event_id` compatibility alias.
- Regression boundary: Rating, scoring, Home favorite club and external ingestion are untouched.
