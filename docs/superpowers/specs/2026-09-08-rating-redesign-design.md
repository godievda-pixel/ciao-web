# Ciao, Web! — Premium Rating & Predictor Profiles Redesign

Date: 2026-09-08
Status: Approved design, pending implementation plan

## Goal

Replace the current Serie A-only seasonal predictor table and the legacy `Общая / Тур / Месяц` scopes with a premium, competition-aware Rating experience covering:

- `Все`
- `Серия А`
- `ЛЧ`
- `ЛЕ`
- `ЛК`
- `Кубок Италии`

The Rating screen must remain visually consistent with Ciao, Web!, but each competition gets its own premium theme. Predictor profiles become full premium profiles with competition-aware statistics and a private-safe history of completed predictions.

## Scope

This change includes:

1. Backend aggregation in the existing `ciao-core-api-fast-v6` Edge Function.
2. Competition-aware seasonal standings.
3. Premium competition-themed Rating UI in the existing `index.html`.
4. Premium predictor profiles opened from a ranking row.
5. Completed-prediction history inside predictor profiles.
6. Server-side protection against exposing another user's future or in-progress predictions.
7. Mobile behavior tuned for Telegram WebView on iPhone and Android.

This change does not introduce a new backend service, new database schema, or a new application route.

## Architecture Decision

Use the existing `ciao-core-api-fast-v6` as the single public backend for Rating and public predictor profiles.

Do not create a separate rating Edge Function and do not calculate combined standings on the frontend.

`ciao-core-api-fast-v6` becomes responsible for:

- reading Serie A settled predictions from `cp_predictions`;
- reading external settled predictions from `cp_external_predictions` joined to `cp_external_matches`;
- normalizing both sources into one internal prediction-result shape;
- calculating all competition-specific and aggregate standings;
- calculating predictor-profile statistics;
- returning only completed/settled prediction history.

The frontend is presentation-only for ranking calculations.

## Active Season

This implementation is explicitly scoped to season `2026/27`.

Backend date boundaries:

- inclusive start: `2026-07-01T00:00:00Z`;
- exclusive end: `2027-07-01T00:00:00Z`.

All standings, trends, streaks, recent summaries and public history must exclude matches outside this window.

The boundaries live as named constants in `ciao-core-api-fast-v6`; no database migration is required. This prevents historical data from a future retained season from being accidentally mixed into 2026/27 standings.

## Competition Keys

Canonical competition values:

- `all`
- `serie_a`
- `ucl`
- `uel`
- `uecl`
- `coppa_italia`

Frontend labels:

- `Все`
- `Серия А`
- `ЛЧ`
- `ЛЕ`
- `ЛК`
- `Кубок Италии`

## Data Sources

### Serie A

Use:

- `cp_predictions`
- `cp_matches`
- `cp_rounds`
- `cp_users`
- `cp_teams`
- existing scoring rules

Only rows where prediction points are calculated are eligible for standings and public history.

Match date for active-season filtering is `cp_matches.kickoff_at` when available, otherwise the associated `cp_rounds.nominal_date`.

### External competitions

Use:

- `cp_external_predictions`
- `cp_external_matches`
- `cp_users`
- `cp_teams` only for a user's favorite club metadata
- existing scoring rules

Competition is derived from `cp_external_matches.competition`.

Only rows with settled/calculated prediction points are eligible for standings and public history.

Match date for active-season filtering is `cp_external_matches.kickoff_at`.

## Standings API

Extend `standings_scope` in `ciao-core-api-fast-v6`.

Request:

```json
{
  "action": "standings_scope",
  "competition": "all"
}
```

Supported values are the six canonical competition keys above.

Legacy `scope=overall|round|month` is no longer used by the new Rating UI. Compatibility may remain temporarily for old callers during rollout, but the new frontend must not expose those controls.

Response shape:

```json
{
  "ok": true,
  "competition": "ucl",
  "standings": [
    {
      "id": 123,
      "display_name": "Daniil",
      "favorite_team": {},
      "rank": 4,
      "points": 42,
      "exact": 5,
      "successful": 12,
      "calculated": 16,
      "success_rate": 75,
      "streak": 3,
      "trend": 2
    }
  ],
  "standings_meta": {
    "competition": "ucl",
    "season": "2026/27",
    "updated_at": "..."
  }
}
```

## Standings Inclusion Rules

All active Ciao users remain visible in every competition table, including users with zero calculated predictions.

This keeps the table stable and complete rather than showing only the subset who happened to predict in a given tournament.

Users with zero calculated predictions have:

- `points = 0`
- `exact = 0`
- `successful = 0`
- `calculated = 0`
- `success_rate = 0`
- `streak = 0`

## Ranking Rules

Primary sort order:

1. points descending;
2. exact-score predictions descending;
3. successful predictions descending;
4. display name ascending.

This order applies consistently to `all` and every individual competition.

## Success Rate

`success_rate` is:

`successful / calculated * 100`

Rounded to the nearest whole percent for API/UI output.

If `calculated = 0`, return `0`.

## Current Streak

The current streak is the number of most recent consecutive calculated predictions in the selected competition where the user earned more than zero points.

The sequence is ordered from newest settled match backward.

For `all`, the sequence merges all eligible competitions chronologically before calculating the streak.

## Trend

Trend represents rank movement compared with the standings immediately before the latest settled competition block.

- positive number = moved up;
- negative number = moved down;
- zero = unchanged or insufficient prior data.

A competition block is defined as the latest coherent settled stage available for that competition:

- Serie A: latest settled round;
- external league-stage competition: latest settled `stage_key` / round block;
- knockout competitions: latest settled stage block;
- `all`: latest settled block chronologically among all competitions.

If a reliable previous block cannot be established, trend is `0` rather than guessed.

## Aggregate `Все`

`all` combines settled Serie A and settled external predictions inside the active 2026/27 season window.

Each prediction is counted exactly once in its native source.

No frontend summation is allowed.

The aggregate uses the same ranking, streak, exact, successful, calculated, success-rate, and trend rules.

## Predictor Profile API

Extend `public_predictor` in `ciao-core-api-fast-v6`.

Request:

```json
{
  "action": "public_predictor",
  "user_id": 123,
  "competition": "ucl",
  "history_limit": 20,
  "history_cursor": null
}
```

`history_limit` defaults to `20` and is clamped to `1..50` server-side.

Response:

```json
{
  "ok": true,
  "predictor": {
    "id": 123,
    "display_name": "Daniil",
    "favorite_team": {},
    "competition": "ucl",
    "stats": {
      "rank": 4,
      "points": 42,
      "exact": 5,
      "successful": 12,
      "calculated": 16,
      "success_rate": 75,
      "streak": 3,
      "trend": 2
    },
    "recent_summary": {
      "sample_size": 10,
      "exact": 3,
      "successful": 7,
      "points": 24
    },
    "history": [],
    "history_page": {
      "next_cursor": null,
      "has_more": false
    }
  }
}
```

## Predictor Profile Behavior

Opening a user from a competition table opens the profile in that same competition context.

The profile contains its own competition switcher with the same six filters:

`Все · Серия А · ЛЧ · ЛЕ · ЛК · Кубок Италии`

Switching competition updates profile statistics and prediction history without closing the profile.

The profile is implemented as a full-height in-app overlay/sheet, not a separate route and not the current small modal. Its own content area scrolls independently while the underlying Rating screen remains frozen. Closing the profile restores the Rating screen at the exact prior scroll position.

## Prediction History

Prediction history is a block inside the predictor profile.

It is not a separate Rating tab or separate route.

History shows only completed and settled predictions from the active 2026/27 season.

Each row includes:

- competition label;
- match date;
- home team;
- away team;
- final score;
- user's historical prediction;
- earned points;
- result quality classification for styling.

Suggested row presentation:

- exact score: premium gold accent;
- correct goal difference/outcome: competition accent;
- miss: muted neutral styling.

For `all`, history is merged chronologically across all competitions.

`recent_summary` is calculated from the latest up to 10 eligible settled predictions in the currently selected competition scope.

## History Privacy / Fairness Rule

`public_predictor` history always returns settled history only, regardless of whether the requested `user_id` belongs to another user or the current user.

Future, open, live, or otherwise unsettled predictions must never be returned from this public-profile endpoint.

This is a server-side rule, not merely a frontend hiding rule.

A manually crafted request for a current prediction must return no current prediction data.

The current user's own open predictions remain available only through the existing authenticated prediction flows, which are not changed by this feature.

## History Pagination

Default page size: 20 rows. Maximum page size: 50 rows.

Use cursor-style pagination based on settled match timestamp plus a stable source-aware tie-break key so Serie A and external rows can coexist without collisions in `all`.

The first profile request returns profile stats plus the first history page.

Loading additional history appends rows without re-rendering or collapsing the profile hero.

## Premium Rating UI

Remove the existing `Общая / Тур / Месяц` scope bar from the active Rating UI.

Top-level Rating switcher:

`Все · Серия А · ЛЧ · ЛЕ · ЛК · Кубок Италии`

The selected competition drives both data and visual theme.

### Competition Themes

#### Все

Ciao premium theme:

- deep navy / near-black background;
- electric blue accent;
- subtle premium blue glow.

#### Серия А

- deep navy;
- Italian/Serie A-inspired cool blue accents;
- restrained cyan-blue glow.

#### ЛЧ

- midnight navy;
- blue-violet / indigo accent;
- cold premium glow.

#### ЛЕ

- graphite / black-navy;
- premium orange accent.

#### ЛК

- graphite / deep green-black;
- green accent.

#### Кубок Италии

- deep blue base;
- restrained green and red Italian accents;
- avoid visually loud tricolor blocks.

Themes modify hero accents, active competition chip, top-3 styling, borders and glow. They do not repaint the entire app or compromise visual consistency with Ciao.

## Rating Hero

The Rating screen begins with a compact premium hero for the current user in the selected competition.

Show:

- current rank;
- total points;
- exact predictions;
- success rate;
- rank movement.

The hero must not dominate the screen vertically.

## Ranking List

Top 3 receive visually stronger premium treatment.

Remaining users use compact rows.

Each row includes, within mobile width constraints:

- rank;
- favorite-club crest if configured;
- display name;
- exact predictions;
- success rate;
- streak;
- trend;
- points.

On narrower phones, secondary metrics may collapse into a compact metadata line, but rank, name and points remain primary.

A ranking row opens the predictor profile.

Favorite-club crest inside the ranking row is visual identity for the predictor; tapping the ranking row should open the predictor profile rather than accidentally opening the club profile.

## Premium Predictor Profile UI

Replace the current small predictor modal with a full-height premium profile overlay suitable for Telegram mobile WebView.

The profile contains:

1. hero with display name and favorite club identity;
2. current rank and points;
3. metric cards for exact, success rate, streak and trend;
4. competition switcher;
5. recent-summary strip;
6. `История прогнозов` block;
7. explicit `Показать ещё` append control when more history is available.

Use an explicit `Показать ещё` control rather than invisible infinite-scroll triggering so loading remains predictable in Telegram WebView.

The selected tournament theme also applies inside the predictor profile.

The profile must have a clear close/back interaction and retain the Rating screen scroll position when closed.

## Loading and Error States

### Rating switch

When switching competition:

- preserve the existing screen shell;
- show skeletons only for the data portion;
- do not blank the entire app;
- if a request fails, retain the previous successful view where possible and show a compact retry state.

### Predictor profile

When first opening:

- profile shell and skeleton may open immediately;
- load stats + first history page;
- if history fails but stats succeed, keep the profile open and show an inline history retry state;
- loading more history must not replace the existing history.

### Empty state

A competition with no settled predictions should show a polished empty state while still showing the full active-user ranking at zero points.

The UI must never show `NaN`, `undefined`, or broken percentages.

## Caching

Backend standings may use the existing short-lived in-memory cache pattern.

Cache keys must include competition and active-season key.

Short TTL around 30 seconds is acceptable for standings and public predictor aggregate stats.

History pages may also be cached briefly, but settlement and active-season checks are part of the query/filter contract and cannot be bypassed by caching.

## Compatibility

The current frontend uses `standings_scope` and `public_predictor` through the core API.

During rollout:

- v6 may keep proxy compatibility for legacy payloads;
- the new frontend switches to competition-aware payloads;
- once deployed, the legacy `Общая / Тур / Месяц` UI is removed from active rendering.

No database migration is required for the design as currently specified.

## Testing Strategy

### Backend contracts

Test:

1. active-season filtering excludes rows outside `2026-07-01 <= match_date < 2027-07-01`.
2. `serie_a` standings use only settled Serie A predictions.
3. `ucl`, `uel`, `uecl`, `coppa_italia` use only the matching external competition.
4. `all` equals the union of settled predictions without duplicates.
5. ranking tie-break order is points → exact → successful → name.
6. zero-activity active users remain present.
7. `success_rate` handles zero safely.
8. streak uses chronological settled results.
9. trend is deterministic and falls back to zero when prior block is unavailable.
10. public history includes completed/settled predictions only.
11. public history never exposes open/live/future predictions, including when requesting one's own public profile.
12. history pagination has stable ordering and no duplicates between pages.
13. `history_limit` is clamped to `1..50`.

### Frontend contracts

Test:

1. six competition filters render and switch data.
2. old `Общая / Тур / Месяц` controls are absent from active Rating.
3. each competition applies the intended premium theme.
4. current-user Rating hero updates per competition.
5. top-3 and regular ranking rows remain readable on iPhone and Android widths.
6. ranking row opens predictor profile in the active competition context.
7. favorite-club crest in the ranking row does not divert the tap into club profile navigation.
8. profile competition switch updates stats and history without closing.
9. `Показать ещё` appends history without collapsing or jumping the profile.
10. closing profile restores Rating scroll position.
11. no current/future prediction is rendered in a public predictor profile.
12. inline JavaScript passes syntax validation.

## Rollout

1. Add backend competition-aware actions to `ciao-core-api-fast-v6` while keeping existing behavior available during transition.
2. Verify backend contract responses against current production data.
3. Implement new Rating frontend in `index.html`.
4. Verify iPhone and Android responsive layouts.
5. Deploy GitHub Pages.
6. Verify production behavior.
7. Remove temporary implementation tooling and temporary spec/plan artifacts from the canonical production tree when implementation is fully complete, restoring the repository requirement that final production tree contains only root `index.html`.

## Success Criteria

The redesign is complete when:

- Rating supports all six competition scopes;
- all statistics are limited to season 2026/27;
- ranking calculations are server-side and consistent across sources;
- the old round/month scope UI is gone;
- each competition has a distinct premium theme without breaking Ciao visual consistency;
- predictor profiles are full-height, premium and competition-aware;
- completed prediction history appears inside user profiles;
- public predictor endpoints cannot retrieve current/future predictions;
- switching competitions and loading history is stable and does not cause visible full-screen jumping;
- the experience works correctly in Telegram WebView on iPhone and Android;
- final production repository tree is restored to root `index.html` only after rollout and verification.
