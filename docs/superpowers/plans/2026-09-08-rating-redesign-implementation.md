# Premium Rating & Predictor Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a competition-aware premium Rating screen for season 2026/27 with six tournament scopes, premium predictor profiles, and server-safe completed-prediction history.

**Architecture:** Extend the existing Supabase Edge Function `ciao-core-api-fast-v6` so standings and public predictor history are calculated server-side from Serie A and external prediction tables. Keep the frontend in the existing root `index.html`, replacing the active `cw18` Rating UI with one competition-aware layer. Temporary test/patch tooling may exist during implementation but must be deleted when rollout is complete.

**Tech Stack:** Supabase Edge Functions (Deno/TypeScript), Supabase Postgres, vanilla HTML/CSS/JavaScript in `index.html`, GitHub Pages, GitHub Actions for one-time TDD patching and syntax checks.

**Spec:** `docs/superpowers/specs/2026-09-08-rating-redesign-design.md`

## Global Constraints

- Canonical production repository is `godievda-pixel/ciao-web`, branch `main`.
- Do not touch `godievda-pixel/ciao-pronostici`.
- Final production tree must contain only root `index.html`; delete spec, plan, workflows and temporary scripts after final verification.
- Active season is `2026/27`, with inclusive start `2026-07-01T00:00:00Z` and exclusive end `2027-07-01T00:00:00Z`.
- Competition keys are exactly `all`, `serie_a`, `ucl`, `uel`, `uecl`, `coppa_italia`.
- Public predictor history must never expose future, open, live or unsettled predictions, even for the current user's public profile.
- Public history defaults to 20 rows and clamps `history_limit` to `1..50`.
- New Rating UI removes the active `Общая / Тур / Месяц` controls.
- Predictor profile is a full-height in-app overlay with its own scroll area and restores Rating scroll position on close.
- Prediction entry, autosave and the working `cw29` score picker must not be modified by Rating work.
- Favorite-club crest in Rating rows is visual identity only; row tap opens predictor profile, not club profile.
- Mobile layout must remain usable in Telegram WebView on iPhone and Android.

---

### Task 1: Competition-aware backend standings

**Files:**
- Temporary create: `tools/cw30_core_v6.ts` — exact candidate source to deploy as `ciao-core-api-fast-v6`.
- Temporary create: `tools/cw30_rating_backend_contract.py` — contract checks for competition keys, season window, aggregation and response fields.
- Modify externally: Supabase Edge Function `ciao-core-api-fast-v6` (`index.ts`).

**Interfaces:**
- Consumes: current v6 proxy/auth/cors behavior and existing v5 compatibility.
- Produces: `standings_scope` with request `{action:'standings_scope', competition}` and response `{ok, competition, standings, standings_meta}`.

- [ ] **Step 1: Write the failing backend contract**

Create `tools/cw30_rating_backend_contract.py` to assert the candidate source contains all six competition keys, season constants, native Serie A and external data queries, `success_rate`, `streak`, `trend`, zero-activity users, and direct `standings_scope` handling in v6 rather than proxying competition-aware calls to v5.

The contract must fail against the current v6 source because current v6 proxies `standings_scope` to v5 and has no competition-aware aggregator.

- [ ] **Step 2: Run RED and confirm expected failure**

Run the contract against the current v6 source snapshot.

Expected: non-zero exit with a message equivalent to `competition-aware standings missing`.

- [ ] **Step 3: Build the minimal v6 standings implementation**

In `tools/cw30_core_v6.ts`, preserve current v6 auth/cors/state/favorite behavior and add named constants:

```ts
const RATING_SEASON='2026/27';
const RATING_SEASON_START='2026-07-01T00:00:00Z';
const RATING_SEASON_END='2027-07-01T00:00:00Z';
const RATING_COMPETITIONS=new Set(['all','serie_a','ucl','uel','uecl','coppa_italia']);
```

Implement one normalized settled-result shape:

```ts
type RatingResult={
  source:'serie_a'|'external';
  competition:'serie_a'|'ucl'|'uel'|'uecl'|'coppa_italia';
  user_id:number;
  source_id:number;
  match_id:number;
  settled_at:string;
  block_key:string;
  points:number;
  base_points:number;
};
```

Load active users once, favorite-club team metadata once, settled Serie A predictions with match/round metadata, and settled external predictions joined to `cp_external_matches`. Filter every result to the season window before aggregation.

Calculate rows with:

```ts
{
  id, display_name, favorite_team,
  rank, points, exact, successful, calculated,
  success_rate, streak, trend
}
```

Use sort order: points desc → exact desc → successful desc → display_name asc.

Keep all active users in every table with zero metrics when they have no settled predictions.

- [ ] **Step 4: Implement deterministic trend**

Define the latest coherent block per competition:

```ts
serie_a => `serie_a:round:${round_number}`
external => `${competition}:stage:${stage_key || stage_order || round_number || 'unknown'}`
```

For `all`, identify the chronologically latest settled block across all included competitions. Recompute standings excluding that block and set `trend = previous_rank - current_rank`; return `0` when no reliable prior block exists.

- [ ] **Step 5: Run GREEN contract**

Run `python tools/cw30_rating_backend_contract.py tools/cw30_core_v6.ts`.

Expected: exit 0 and explicit checks for season constants, six scopes, combined aggregation, success rate, streak, trend and zero-user inclusion.

- [ ] **Step 6: Deploy candidate v6 source**

Deploy `tools/cw30_core_v6.ts` to Supabase project `dkefzepiiudehhzbbrjn` as `ciao-core-api-fast-v6`, preserving `verify_jwt=false` because the current function implements custom Telegram authentication/proxy semantics.

- [ ] **Step 7: Verify production data invariants with SQL**

Run read-only SQL proving:

```sql
-- active users exist
select count(*) from cp_users where is_active=true;

-- external competition keys are exactly the expected set currently present
select competition,count(*) from cp_external_matches group by competition order by competition;

-- no calculated rows outside the season are included in expected aggregates
```

Also compare a direct SQL aggregate for at least Serie A and one external competition with the backend's expected ranking formula.

- [ ] **Step 8: Commit temporary backend implementation state**

Commit the temporary candidate/test files only while implementation continues. They are removed in Task 5.

---

### Task 2: Public predictor profile and completed history backend

**Files:**
- Modify temporary: `tools/cw30_core_v6.ts`.
- Modify temporary: `tools/cw30_rating_backend_contract.py`.
- Modify externally: Supabase Edge Function `ciao-core-api-fast-v6`.

**Interfaces:**
- Consumes: Task 1 normalized `RatingResult[]` and competition standings helper.
- Produces: `public_predictor` request `{action:'public_predictor', user_id, competition, history_limit, history_cursor}` and response `{ok,predictor}` with `stats`, `recent_summary`, `history`, `history_page`.

- [ ] **Step 1: Extend RED contract for public history**

Add failing assertions requiring:

```ts
history_limit clamp 1..50
history_cursor parsing
settled-only history filtering
season-window filtering
source-aware cursor key
recent_summary from latest up to 10 eligible rows
```

Expected: current Task 1 candidate fails because history support is absent.

- [ ] **Step 2: Implement normalized history rows**

Return rows shaped as:

```ts
{
  key:string,
  competition:string,
  competition_label:string,
  settled_at:string,
  home_name:string,
  away_name:string,
  final_home:number,
  final_away:number,
  prediction_home:number,
  prediction_away:number,
  points:number,
  base_points:number,
  quality:'exact'|'success'|'miss'
}
```

For Serie A, require calculated prediction points and finished/settled match result metadata. For external competitions, require `cp_external_predictions.points is not null` and a settled/finalized external match with final scores present.

- [ ] **Step 3: Implement cursor pagination**

Use a stable descending cursor from `settled_at + source-aware key` such as:

```ts
`${settled_at}|${source}:${source_id}`
```

Encode/decode as URL-safe base64 text. Fetch `limit + 1`, return at most `limit`, set `has_more`, and set `next_cursor` from the final emitted row.

- [ ] **Step 4: Implement predictor stats and recent summary**

Use the same competition-aware standings helper for profile `stats`, ensuring the rank is identical to the Rating table.

Compute `recent_summary` over the latest up to 10 eligible history rows:

```ts
{ sample_size, exact, successful, points }
```

- [ ] **Step 5: Add privacy contract**

The public profile query path must start from settled/calculated predictions only. Do not query or serialize open prediction rows and then hide them later.

The contract must explicitly reject source patterns that select all predictions without a calculated/settled filter for public history.

- [ ] **Step 6: Run GREEN backend contract and redeploy**

Run the complete contract, then redeploy v6.

Expected: all standings and history checks pass.

- [ ] **Step 7: Validate history safety with SQL fixtures already in production**

Use read-only SQL to confirm there are open/future predictions in source tables that are excluded by the exact predicates used for public history, and confirm calculated history rows have final scores.

---

### Task 3: Premium competition-aware Rating screen

**Files:**
- Modify: `index.html`.
- Temporary create: `tools/cw31_rating_frontend.py` — deterministic patch script.
- Temporary create: `.github/workflows/rating-frontend.yml` — RED/GREEN patch workflow.

**Interfaces:**
- Consumes: `standings_scope` from Task 1.
- Produces: active Rating UI with six competition filters and current-user hero.

- [ ] **Step 1: Write RED frontend contract**

The one-time workflow must fail before patching unless all of these are true:

```text
six competition keys exist in Rating state
active Rating contains no data-cw18-scope overall/round/month controls
Rating requests standings_scope with competition
premium theme classes exist for all six competitions
row click still uses predictor profile navigation
```

Run RED before the patch and require failure.

- [ ] **Step 2: Introduce one canonical Rating state layer**

Add a new versioned source block inside the active app IIFE, not as an external global override. Define:

```js
let __cw30RatingCompetition='all';
let __cw30RatingLoading=false;
let __cw30RatingError='';
const __cw30RatingLabels={all:'Все',serie_a:'Серия А',ucl:'ЛЧ',uel:'ЛЕ',uecl:'ЛК',coppa_italia:'Кубок Италии'};
```

Do not create duplicate late implementations of the same functions.

- [ ] **Step 3: Replace the legacy Rating controls**

Render a horizontally scrollable competition switcher in this exact order:

```text
Все · Серия А · ЛЧ · ЛЕ · ЛК · Кубок Италии
```

Remove active `Общая / Тур / Месяц` rendering from Rating.

- [ ] **Step 4: Implement competition themes**

Use a root Rating wrapper like:

```html
<section class="cw30-rating cw30-theme-ucl">...</section>
```

Provide CSS variables per theme for accent, glow, border, hero gradient and top-3 highlight. Themes should be restrained and scoped to Rating/profile, not repaint the whole app.

- [ ] **Step 5: Implement the current-user premium hero**

Find the row where `row.id === S.user.id` and show compact metrics:

```text
Место · Очки · Точные · Успешность · Динамика
```

When no settled predictions exist, show valid zeros and no `NaN`.

- [ ] **Step 6: Implement premium ranking rows**

Top 3 get distinct premium card treatment. Remaining rows stay compact. Always keep rank, name and points primary; on narrow phones collapse exact / success rate / streak / trend into one metadata line.

Favorite crest must not carry club navigation attributes in this Rating renderer.

- [ ] **Step 7: Implement competition switching**

On switch:

```js
POST {action:'standings_scope', competition:key}
```

Keep the screen shell visible, replace only the data area with skeleton state, retain previous successful rows if the request fails, and expose a compact retry action.

- [ ] **Step 8: Run GREEN and syntax checks**

Require the frontend contract to pass and run `node --check` against every inline `<script>` extracted from `index.html`.

- [ ] **Step 9: Commit the frontend Rating patch and self-delete workflow tooling**

The one-time workflow commits `index.html` and removes its own workflow/patch script. Keep the spec/plan until Task 5 final cleanup.

---

### Task 4: Premium predictor overlay with in-profile prediction history

**Files:**
- Modify: `index.html`.
- Temporary create: `tools/cw32_predictor_profile.py`.
- Temporary create: `.github/workflows/predictor-profile.yml`.

**Interfaces:**
- Consumes: `public_predictor` from Task 2 and current Rating competition from Task 3.
- Produces: full-height predictor overlay, six-scope switcher, stats, recent summary and appendable completed history.

- [ ] **Step 1: Write RED predictor-profile contract**

Require failure before patching unless active source contains:

```text
full-height overlay class
competition passed into public_predictor
История прогнозов
Показать ещё
history_cursor append logic
no rendering path for open/live/future public predictions
scroll restoration state
```

- [ ] **Step 2: Replace the small predictor modal**

Implement an overlay fixed to the app viewport with its own header/back button and scroll container. Save Rating `main.scrollTop` before opening; freeze the underlying Rating area while open; restore the exact saved scroll position on close.

- [ ] **Step 3: Open profile in the current competition context**

Ranking row tap calls:

```js
__cw30OpenPredictor(userId, __cw30RatingCompetition)
```

First request:

```js
{action:'public_predictor',user_id:userId,competition,history_limit:20,history_cursor:null}
```

- [ ] **Step 4: Render the premium profile hero and metrics**

Show display name, favorite club identity, rank, points, exact, success rate, streak and trend. Apply the same tournament theme used by the selected profile competition.

- [ ] **Step 5: Add the profile competition switcher**

Use the same six keys/order as Rating. Switching profile competition keeps the overlay open, shows skeletons only for the profile data region, resets history cursor, and requests the new competition.

- [ ] **Step 6: Render `История прогнозов` inside the profile**

Each row shows competition/date, teams, final score, user's historical score, and points. Styling:

```text
exact => gold accent
success => active competition accent
miss => muted neutral
```

Do not display any row without a final score and calculated points.

- [ ] **Step 7: Implement recent summary and `Показать ещё`**

Show:

```text
Последние N · точных X · успешных Y · Z очков
```

When `history_page.has_more` is true, render `Показать ещё`. Request with `next_cursor` and append returned rows to the existing history DOM/state without rebuilding the hero or resetting overlay scroll.

- [ ] **Step 8: Implement partial-error behavior**

If first profile load fails, show a retry state inside the overlay. If an append request fails, preserve existing history and show retry only beside the load-more area.

- [ ] **Step 9: Run GREEN, syntax and interaction contracts**

Contract must verify profile context switching, history append markers, scroll restoration and absence of legacy small predictor modal in active rendering. Run inline JavaScript syntax checks.

- [ ] **Step 10: Commit profile patch and self-delete workflow tooling**

Commit only `index.html` plus still-temporary spec/plan docs.

---

### Task 5: Production verification, mobile stability and repository cleanup

**Files:**
- Verify: `index.html`.
- Delete: `tools/cw30_core_v6.ts` if still present.
- Delete: `tools/cw30_rating_backend_contract.py` if still present.
- Delete: `docs/superpowers/specs/2026-09-08-rating-redesign-design.md`.
- Delete: `docs/superpowers/plans/2026-09-08-rating-redesign-implementation.md`.
- Delete: any remaining temporary `.github/workflows/*` or `tools/*` created for this redesign.

**Interfaces:**
- Consumes: completed backend and frontend tasks.
- Produces: verified production build with final repository tree containing only `index.html`.

- [ ] **Step 1: Verify backend health and active version**

Confirm `ciao-core-api-fast-v6` is ACTIVE, custom auth behavior remains enabled, and GET health reports the new rating capability/version marker without regressing existing v6 state behavior.

- [ ] **Step 2: Verify database-level expected aggregates**

For at least two users, compute expected Serie A and `all` totals via read-only SQL from settled season rows and compare with the corresponding app/API values observed through the production UI.

- [ ] **Step 3: Verify six Rating scopes in Telegram WebView**

Check all six filters switch successfully and the competition theme changes without a full-app reload. Confirm zero-data external scopes render polished zero standings rather than errors.

- [ ] **Step 4: Verify predictor history privacy and content**

Open at least two predictor profiles. Confirm only completed history appears, profile starts in the ranking's competition, switching competition keeps the profile open, and `Показать ещё` appends rather than replaces.

- [ ] **Step 5: Verify mobile layouts**

At widths representative of iPhone and Android Telegram WebViews, verify:

```text
no horizontal page overflow
competition chips remain scrollable
rank/name/points remain visible
profile close/back is reachable
history rows do not overflow
bottom navigation remains usable after closing profile
```

- [ ] **Step 6: Regression-check Predictions**

Confirm the working `cw29` score picker still opens 0–9, score selection updates the card, and autosave status progresses through changed/saving/saved. Rating work must not alter these functions.

- [ ] **Step 7: Run final syntax and source-order checks**

Run inline `node --check` for all scripts and a source contract that asserts only one active Rating implementation and one active predictor-profile implementation exist.

- [ ] **Step 8: Deploy GitHub Pages and wait for successful deployment**

Confirm the Pages workflow for the final production commit completes with `conclusion: success`.

- [ ] **Step 9: Remove all temporary implementation artifacts**

Delete spec, plan, test scripts and workflows from `main` only after verification has passed.

- [ ] **Step 10: Verify final repository invariant**

Fetch the recursive tree for final `main` and require exactly one production file:

```text
index.html
```

No `docs/`, `.github/`, `tools/`, `src/`, `dist/` or other files may remain.

- [ ] **Step 11: Final production report**

Report the final commit SHA, active v6 Edge Function version, Pages deployment run ID, backend verification summary, frontend verification summary, and explicitly note that `index.html` is the only remaining repository file.
