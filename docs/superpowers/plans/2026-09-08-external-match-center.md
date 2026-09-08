# External Match Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the existing full BSD-powered Match Center to UCL, UEL, UECL and Coppa Italia, with tournament-specific visual themes, while preserving Serie A Match Center and prediction editing behavior.

**Architecture:** Keep one Match Center UI and one backend family, but make identity/source explicit with `source: 'serie_a' | 'external'`. Normalize `cp_matches` and `cp_external_matches` into one response shape, use a physically separate cache table for external matches, and propagate `matchViewSource` through frontend navigation, polling, lazy sections and session restore.

**Tech Stack:** Supabase Postgres, Supabase Edge Functions (Deno + `@supabase/supabase-js`), BSD Sports API, single-file GitHub Pages frontend (`index.html`), vanilla JavaScript/CSS, GitHub Actions for temporary source-contract checks.

**Spec:** `docs/superpowers/specs/2026-09-08-external-match-center-design.md`

## Global Constraints

- Production repository is `godievda-pixel/ciao-web`, branch `main`.
- Do not touch archive/fallback repository `godievda-pixel/ciao-pronostici`.
- Final accepted production tree must return to root `index.html` only; spec/plan/workflow/test artifacts are temporary.
- Existing Serie A Match Center remains functionally unchanged except for explicit source plumbing.
- Existing `cw29` score picker and prediction autosave must remain unchanged.
- Club profile navigation remains disabled inside Predictions.
- External Match Center must never render “Контекст Серии А”.
- External identities are always `(source, match_id)`, never numeric `match_id` alone.
- Optional BSD sections must fail locally without replacing the whole Match Center.
- The unrelated Rating rank inconsistency is out of scope for this feature.

---

## File / Service Map

- **Database:** create `public.cp_external_match_center_cache` only.
- **Edge Function:** modify deployed function `ciao-match-summary-fast-v2` to normalize internal/external match summaries and prediction split.
- **Edge Function:** modify deployed function `ciao-match-center-fast-v3` to normalize internal/external full/lazy data and use source-specific cache storage.
- **Frontend:** modify `index.html` only for source-aware Match Center state/API/navigation, external card entry points, external crest rendering and tournament theme CSS.
- **Temporary tests/tooling:** one-time workflow/scripts may be added under `.github/workflows/` or `scripts/`, but must self-delete or be removed after visual acceptance.

---

### Task 1: External Match Center Cache Table

**Files / Services:**
- Modify: Supabase schema for project `dkefzepiiudehhzbbrjn`
- Create: `public.cp_external_match_center_cache`

**Interfaces:**
- Consumes: `public.cp_external_matches(id, provider_event_id)`
- Produces: external cache rows keyed by `external_match_id`

- [ ] **Step 1: Run the failing schema contract**

Run:

```sql
select to_regclass('public.cp_external_match_center_cache') as cache_table;
```

Expected before migration: `cache_table = null`.

- [ ] **Step 2: Apply the migration**

Run as a named migration:

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

Do not add anon/authenticated policies; Edge Functions use the service role and are the only intended writers/readers.

- [ ] **Step 3: Run the GREEN schema contract**

Run:

```sql
select
  to_regclass('public.cp_external_match_center_cache') as cache_table,
  c.relrowsecurity as rls_enabled
from pg_class c
where c.oid = 'public.cp_external_match_center_cache'::regclass;
```

Expected: table exists and `rls_enabled = true`.

- [ ] **Step 4: Verify FK isolation**

Run:

```sql
select
  conname,
  pg_get_constraintdef(oid) as definition
from pg_constraint
where conrelid = 'public.cp_external_match_center_cache'::regclass;
```

Expected: FK references `cp_external_matches(id)`, not `cp_matches(id)`.

---

### Task 2: Source-Aware Summary API

**Files / Services:**
- Modify deployed Edge Function: `ciao-match-summary-fast-v2/index.ts`

**Interfaces:**
- Consumes request: `{ source?: 'serie_a'|'external', match_id: number }`
- Produces normalized response: `{ ok, source, match, competition, stage, prediction_split, status, summary_only, recommended_poll_ms }`

- [ ] **Step 1: RED — prove current summary endpoint is internal-only**

Inspect current source and assert all three are true:

```text
getMatch() reads only cp_matches
getSplit() reads only cp_predictions
request body has no source branch
```

Also select one real external ID for later smoke:

```sql
select id, competition, provider_event_id
from cp_external_matches
order by id
limit 1;
```

- [ ] **Step 2: Add canonical source parser**

Add:

```ts
function sourceOf(body:any){
  return String(body?.source??'serie_a')==='external' ? 'external' : 'serie_a';
}
```

- [ ] **Step 3: Add normalized internal/external loaders**

Implement two source branches that both return a normalized match object.

Internal shape must include:

```ts
{
  id, source:'serie_a', competition:'serie_a',
  provider_event_id: bsd_event_id,
  bsd_event_id,
  kickoff_at, home_score, away_score,
  is_finished, live_status, live_elapsed,
  round,
  home:{id,bsd_team_id,name,short_name,custom_emoji_id,crest_url:null,country_code:null},
  away:{...},
  prediction
}
```

External shape must include:

```ts
{
  id, source:'external', competition,
  provider_event_id,
  bsd_event_id: provider_event_id,
  stage_key, stage_label, stage_order, round_number,
  kickoff_at, home_score, away_score,
  is_finished: status==='finished',
  live_status: status,
  live_elapsed: minute,
  home:{id:null,bsd_team_id:home_bsd_team_id,name:home_name,short_name:null,custom_emoji_id:null,crest_url:home_crest_url,country_code:home_country_code},
  away:{...},
  prediction
}
```

External current-user prediction query:

```ts
db.from('cp_external_predictions')
  .select('home_score,away_score,points,updated_at')
  .eq('user_id', userId)
  .eq('external_match_id', matchId)
  .maybeSingle()
```

- [ ] **Step 4: Make prediction split source-aware**

For `serie_a`, retain `cp_predictions.match_id`.

For `external`, query:

```ts
db.from('cp_external_predictions')
  .select('home_score,away_score')
  .eq('external_match_id', matchId)
```

Cache key must include source:

```ts
const splitKey = `${source}:${matchId}`;
```

- [ ] **Step 5: Normalize statuses**

Use explicit external mapping:

```ts
function externalStatus(s:string){
  const x=String(s||'').toLowerCase();
  if(['live','halftime','extra_time','penalties'].includes(x)) return 'live';
  if(x==='finished') return 'finished';
  return 'upcoming';
}
```

Keep original DB status available on `match.live_status` for presentation of postponed/cancelled when needed.

- [ ] **Step 6: Return explicit source/competition/stage**

Response must include:

```ts
{
  ok:true,
  source,
  match,
  competition:match.competition,
  stage: source==='external' ? {
    key:match.stage_key,
    label:match.stage_label,
    order:match.stage_order,
    round_number:match.round_number
  } : null,
  prediction_split,
  status,
  summary_only:true,
  recommended_poll_ms
}
```

- [ ] **Step 7: GREEN source contract**

Re-read deployed source and assert:

```text
cp_external_matches is referenced
cp_external_predictions is referenced twice (user prediction + split)
request source defaults to serie_a
cache keys include source
external response exposes competition/stage
```

- [ ] **Step 8: Deploy and record the new active function version**

Deploy same slug `ciao-match-summary-fast-v2`, preserving `verify_jwt=false` because custom Telegram validation remains in function body.

---

### Task 3: Source-Aware Full/Lazy Match Center API

**Files / Services:**
- Modify deployed Edge Function: `ciao-match-center-fast-v3/index.ts`

**Interfaces:**
- Consumes request: `{ source?: 'serie_a'|'external', match_id: number, sections?: string[], include_split?: boolean }`
- Produces same normalized `match`/metadata as Task 2 plus lazy BSD sections.

- [ ] **Step 1: RED — prove current full endpoint is internal-only**

Inspect current source and assert:

```text
loadMatch() reads only cp_matches
predictionSplit() reads only cp_predictions
all cache helpers are hardcoded to cp_match_center_cache + match_id
fetchOverviewMeta() assumes match.bsd_event_id
```

- [ ] **Step 2: Add source-aware normalized loader**

Reuse the exact normalized match shape from Task 2. Do not invent a second frontend shape.

- [ ] **Step 3: Add cache descriptor**

Add:

```ts
function cacheSpec(source:string){
  return source==='external'
    ? {table:'cp_external_match_center_cache', key:'external_match_id', event:'provider_event_id'}
    : {table:'cp_match_center_cache', key:'match_id', event:'bsd_event_id'};
}
```

Update `ensureCacheRow`, `readCache`, `claimRefresh`, `waitForRefresh` and final `upsert` to receive `(source, matchId)` and use the descriptor.

- [ ] **Step 4: Make refresh-flight key collision-safe**

Replace keys like:

```ts
`${match.id}:${sections}`
```

with:

```ts
`${match.source}:${match.id}:${[...sections].sort().join(',')}`
```

- [ ] **Step 5: Make BSD event access source-neutral**

All BSD routes must use:

```ts
const eventId = Number(match.provider_event_id ?? match.bsd_event_id);
```

`fetchOverviewMeta()` must use normalized `match.home.bsd_team_id` and `match.away.bsd_team_id`, not `cp_teams` assumptions.

- [ ] **Step 6: Make prediction split source-aware**

Use the same source split logic as Task 2 and a source-qualified cache key.

- [ ] **Step 7: Preserve graceful section degradation**

Keep the existing independent section refresh model for:

```text
detail, stats, incidents, lineups, player_stats, overview_meta
```

A failed BSD section updates only `payload.errors[key]`; cached successful sections remain in response.

- [ ] **Step 8: Return normalized source metadata**

Full response includes:

```ts
source,
competition:match.competition,
stage: match.source==='external' ? {...} : null
```

alongside existing coverage/detail/stats/incidents/lineups/player_stats/overview_meta/errors fields.

- [ ] **Step 9: GREEN source contract**

Re-read source and verify:

```text
both cp_matches and cp_external_matches loaders exist
external cache table is used only for source external
source participates in flight/split/cache identity
all BSD routes use normalized provider event ID
no fallback from missing external match to cp_matches exists
```

- [ ] **Step 10: Deploy and record the new active function version**

Deploy same slug `ciao-match-center-fast-v3`, preserving current custom Telegram auth and `verify_jwt=false`.

---

### Task 4: Backend Data/Collision Smoke Contracts

**Files / Services:**
- Read-only SQL against Supabase production data
- Read deployed Task 2/3 sources

**Interfaces:**
- Proves backend has valid provider linkage for all supported competitions.

- [ ] **Step 1: Verify provider coverage remains complete**

Run:

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

Expected current counts:

```text
coppa_italia 12/12/12/12
ucl          32/32/32/32
uecl          8/8/8/8
uel          16/16/16/16
```

- [ ] **Step 2: Find a numeric ID collision candidate**

Run:

```sql
select e.id,
       e.competition,
       e.home_name as external_home,
       e.away_name as external_away,
       m.id as serie_a_id
from cp_external_matches e
join cp_matches m on m.id=e.id
order by e.id
limit 1;
```

Expected: at least one overlapping numeric ID is acceptable and must resolve differently by source.

- [ ] **Step 3: Verify prediction table isolation**

For one external match with predictions, compare counts:

```sql
select
  (select count(*) from cp_external_predictions where external_match_id = :external_id) as external_predictions,
  (select count(*) from cp_predictions where match_id = :external_id) as serie_a_predictions_same_numeric_id;
```

The two values are independent; backend source determines which one is used.

- [ ] **Step 4: Verify no external cache row can satisfy an internal lookup**

Check both cache tables independently for the collision ID. Physical table separation is the contract.

---

### Task 5: Frontend Match Center Source Plumbing

**Files:**
- Modify: `index.html`
- Temporary test: `.github/workflows/external-match-center-frontend-tdd.yml` or equivalent one-time contract runner

**Interfaces:**
- Produces frontend state variable `matchViewSource` and source-aware API helpers.
- Legacy callers remain valid because default source is `serie_a`.

- [ ] **Step 1: RED frontend contract**

Create/run a one-time source test that fails unless all are present:

```text
let matchViewSource
openMatchCenter(id, source='serie_a') or equivalent defaulting behavior
summary request includes source
lazy section request includes source
session persistence includes matchViewSource
```

Expected before patch: FAIL.

- [ ] **Step 2: Add source state**

Near existing Match Center state, add:

```js
let matchViewSource='serie_a';
```

Keep `matchViewId` numeric.

- [ ] **Step 3: Make summary/full helpers source-aware**

Change conceptual helpers to:

```js
const __cw9FastMatchApi=(id,sections=[],source=matchViewSource)=>
  __cw9Post(__CW9_MATCH_API,{source,match_id:Number(id),sections,include_split:false},'Не удалось загрузить Матч-центр');

const __cw9SummaryApi=(id,source=matchViewSource)=>
  __cw9Post(__CW9_SUMMARY_API,{source,match_id:Number(id)},'Не удалось загрузить матч');
```

Every refresh/lazy call must either rely on `matchViewSource` or pass it explicitly.

- [ ] **Step 4: Update open/close contract**

Canonical open signature:

```js
openMatchCenter=async function(id,source='serie_a'){
  matchViewSource=source==='external'?'external':'serie_a';
  matchViewId=Number(id);
  ...
}
```

On close, reset only after return state is captured:

```js
matchViewSource='serie_a';
```

- [ ] **Step 5: Persist/restore source**

Add `matchViewSource` to the session snapshot and restore it before calling `openMatchCenter`.

- [ ] **Step 6: Preserve source through club-profile round trips**

Any snapshot that currently stores `matchViewId`/`matchCenterTab` must also store `matchViewSource` so a Serie A match remains Serie A and a future external-club route cannot collide.

- [ ] **Step 7: GREEN + syntax check**

Extract all inline `<script>` bodies from `index.html` into a temporary JS file and run:

```bash
node --check /tmp/ciao-inline.js
```

Also assert source plumbing markers exist exactly once in the active layer.

---

### Task 6: External Entry Points From Matches and Predictions

**Files:**
- Modify: `index.html`

**Interfaces:**
- External cards call `openMatchCenter(externalId,'external')`.
- Prediction editing controls never trigger Match Center.

- [ ] **Step 1: RED — external cards have no Match Center locator**

Source contract must fail unless external cards expose a stable external match ID and source.

- [ ] **Step 2: Add source/id data attributes to external cards**

Both external edit and mine cards include data equivalent to:

```html
data-cwpred-match="42" data-match-source="external"
```

Matches-tab external cards use equivalent attributes.

- [ ] **Step 3: Bind Matches cards**

On free card tap:

```js
openMatchCenter(Number(card.dataset.externalMatchId),'external')
```

Do not intercept tournament/stage controls.

- [ ] **Step 4: Bind Predictions cards with hard interaction guard**

Guard must ignore clicks originating from:

```js
'.cw29-score-pick, #cw29-score-picker, button, [data-cwpred-action], [data-cwpred-pick]'
```

Then call external Match Center only for free card space.

- [ ] **Step 5: Verify `cw29` picker regression contract**

Static/source checks must confirm:

```text
one canonical cw29 picker implementation remains
no cw28 picker classes are reintroduced
score digit handler still schedules existing autosave
external card click guard contains cw29-score-pick
```

- [ ] **Step 6: Run inline JS syntax check again**

Expected: `node --check` exits 0.

---

### Task 7: External Match Center Presentation and Tournament Themes

**Files:**
- Modify: `index.html`

**Interfaces:**
- Uses normalized `match.source`, `competition`, `stage_label`, `crest_url` from Tasks 2/3.

- [ ] **Step 1: RED — external presentation contract**

Fail unless source contains competition theme mapping for all four keys:

```text
ucl, uel, uecl, coppa_italia
```

and a source guard around Serie A context.

- [ ] **Step 2: Make team logo renderer source-neutral**

Use priority:

```js
if(t?.crest_url) return `<img ... src="${esc(t.crest_url)}">`;
if(t?.custom_emoji_id) return existing Telegram emoji renderer;
return football fallback;
```

External crest CSS must fix width/height and use `object-fit:contain`.

- [ ] **Step 3: Add competition metadata helpers**

Mapping:

```js
const labels={
  ucl:'Лига чемпионов',
  uel:'Лига Европы',
  uecl:'Лига конференций',
  coppa_italia:'Кубок Италии'
};
```

External hero subtitle:

```js
`${labels[d.competition]||'Матч'}${d.stage?.label?' · '+d.stage.label:''}`
```

Serie A keeps round/date copy.

- [ ] **Step 4: Hard-disable Serie A context for external source**

At the start of `__cw18MatchContext` or its active successor:

```js
if(String(d?.source||d?.match?.source||'serie_a')!=='serie_a') return '';
```

Do not hide the context with CSS; do not run Serie A table/club lookups for external render.

- [ ] **Step 5: Add theme classes**

Match Center shell gets one class based on competition, e.g.:

```text
mc-theme-ucl
mc-theme-uel
mc-theme-uecl
mc-theme-coppa
```

Theme token intent:

```text
UCL: midnight/navy + violet/electric-blue glow
UEL: graphite + orange
UECL: graphite + saturated green
Coppa: deep navy + restrained green/red accents
```

Only hero decoration, badges, active tabs, borders and subtle glow change; layout stays shared.

- [ ] **Step 6: Keep all existing tabs/data components**

No separate external implementations of Overview/Stats/Events/Lineups/Players. Reuse existing renderers against normalized BSD payloads.

- [ ] **Step 7: GREEN + syntax contract**

Verify:

```text
all four theme classes exist
external hero uses tournament + stage
Serie A context has a source guard
crest_url precedes custom_emoji_id in logo selection
node --check exits 0
```

---

### Task 8: Production Verification and Rollout

**Files / Services:**
- `index.html`
- deployed summary/full Match Center functions
- GitHub Pages deployment

**Interfaces:**
- Produces production-ready feature for Telegram Mini App validation.

- [ ] **Step 1: Verify current `main` backup point exists**

Create or update a stable backup branch from the pre-frontend-change commit before committing the final frontend patch.

- [ ] **Step 2: Run full static frontend contract**

Required assertions:

```text
matchViewSource exists
legacy Serie A callers default to serie_a
all external card entry points call source external
cw29 picker implementation unchanged
no cw28 picker layer
external context guard present
all four theme mappings present
```

- [ ] **Step 3: Run inline JavaScript syntax verification**

Run `node --check` against concatenated inline scripts. Expected exit 0.

- [ ] **Step 4: Re-read deployed Edge Function versions**

Confirm active sources contain:

```text
source-aware external loaders
external prediction tables
external cache table
source-qualified cache/flight keys
```

- [ ] **Step 5: Verify database cache/RLS state**

Confirm `cp_external_match_center_cache` exists, RLS enabled, FK points to `cp_external_matches`.

- [ ] **Step 6: Commit the frontend patch**

Commit message:

```text
feat: add external tournament match centers
```

- [ ] **Step 7: Verify GitHub Pages deployment**

Wait for Pages build/deploy success on the exact frontend commit SHA.

- [ ] **Step 8: Telegram Mini App visual smoke**

User validates at least:

```text
one UCL Match Center
one UEL/UECL or Coppa Match Center
external Match Center has no “Контекст Серии А”
Serie A Match Center still works
score picker still opens and autosaves
back returns to the same tournament/stage/scroll
```

- [ ] **Step 9: Cleanup only after user acceptance**

Delete temporary workflows/tests/spec/plan artifacts and verify the final production repository tree again contains only root `index.html`.

---

## Self-Review Checklist

- Spec coverage: backend source identity, separate cache, normalized data, external prediction split, entry points, picker guard, themes, context removal, navigation restore, lazy/live refresh, graceful degradation and cleanup are each assigned to a task.
- Placeholder scan: no implementation steps rely on TBD/TODO language.
- Type consistency: every layer uses `source: 'serie_a'|'external'`; frontend state is `matchViewSource`; external primary key remains numeric `matchViewId`; normalized provider event is `provider_event_id` with `bsd_event_id` compatibility alias.
- Regression boundary: Rating, prediction scoring, Home favorite club and external ingestion are explicitly untouched.
