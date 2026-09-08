# External Match Center — Design Spec

Date: 2026-09-08
Project: Ciao, Web!
Repository: `godievda-pixel/ciao-web`
Status: approved design, implementation not started

## Goal

Add the existing full Match Center experience to all external competitions already supported by Predictions and Matches:

- UEFA Champions League (`ucl`)
- UEFA Europa League (`uel`)
- UEFA Conference League (`uecl`)
- Coppa Italia (`coppa_italia`)

The external Match Center must reuse the same BSD-powered match data pipeline as Serie A where possible, while remaining isolated from Serie A-specific database relationships and UI context.

## Product requirements

### Entry points

External Match Center opens from:

1. **Matches** — tapping an external match card opens the Match Center.
2. **Predictions** — tapping free space on an external prediction card opens the Match Center.

Inside Predictions, score controls remain dedicated to prediction editing. Tapping either `cw29` score digit, the picker, or any prediction action must **not** open Match Center.

### Serie A behavior

Serie A Match Center remains functionally unchanged.

The existing **“Контекст Серии А”** block remains available only for Serie A matches.

### External behavior

For UCL / UEL / UECL / Coppa Italia:

- no “Контекст Серии А” block;
- hero displays tournament + stage instead of Serie A round context;
- all available BSD match data is used;
- existing Match Center tabs are retained:
  - Обзор
  - Статистика
  - События
  - Составы
  - Игроки

Available sections continue to degrade gracefully if BSD does not provide a data set.

## Visual themes

Match Center uses one shared layout and typography system, with competition-specific theme tokens.

### Serie A

Keep the current existing Match Center theme.

### Champions League

- deep midnight-blue foundation;
- violet / electric-blue glow;
- cool bright accent for active controls and live states.

### Europa League

- graphite / near-black foundation;
- orange accent;
- subtle warm glow.

### Conference League

- dark graphite foundation;
- saturated green accent;
- restrained green glow.

### Coppa Italia

- deep navy foundation;
- restrained green/red Italian accents;
- blue remains the primary structural color so the screen does not become visually noisy.

Only theme tokens, hero decoration, active tabs, borders, badges and subtle glow change. Layout remains consistent across tournaments.

## External match identity

Internal and external tables both use numeric primary keys, so numeric `match_id` alone is not a globally safe identity.

Canonical frontend Match Center identity is:

- `matchViewSource`: `serie_a | external`
- `matchViewId`: numeric table primary key

All Match Center requests include both values.

Examples:

```json
{ "source": "serie_a", "match_id": 15 }
```

```json
{ "source": "external", "match_id": 15 }
```

These are distinct matches.

The same pair is persisted in session restore and all return-navigation state.

## Backend architecture

### Chosen approach

Extend the existing Match Center backend family to understand two sources instead of creating a separate external Match Center service.

Primary endpoints to extend:

- `ciao-match-summary-fast-v2`
- `ciao-match-center-fast-v3`

New deployed versions may keep the same slugs; frontend contracts remain explicit through the `source` request field.

### Source resolution

#### `source = serie_a`

Existing behavior:

- match: `cp_matches`
- teams: `cp_teams`
- prediction: `cp_predictions`
- prediction split: `cp_predictions`
- provider event: `bsd_event_id`
- cache: `cp_match_center_cache`
- Serie A round metadata remains available.

#### `source = external`

New behavior:

- match: `cp_external_matches`
- prediction: `cp_external_predictions`
- prediction split: `cp_external_predictions`
- provider event: `provider_event_id`
- home/away team presentation is built directly from external columns:
  - BSD team ID
  - name
  - country code
  - crest URL
- competition and stage metadata come from `cp_external_matches`;
- cache: new `cp_external_match_center_cache`.

Every existing external match currently has a provider event ID and both BSD team IDs, so all 68 current external matches are eligible for Match Center.

## Canonical response shape

Both sources return a normalized frontend-facing object with the same high-level shape:

```text
ok
source
match
competition
stage
prediction_split
status
recommended_poll_ms
coverage
detail
stats
incidents
lineups
player_stats
overview_meta
errors
```

### Normalized `match`

Common fields:

- `id`
- `source`
- `kickoff_at`
- `home_score`
- `away_score`
- status / live minute fields
- `is_finished`
- `provider_event_id`
- `home`
- `away`
- `prediction`

Normalized team fields:

- `id` when a stable local ID exists, otherwise `null`
- `bsd_team_id`
- `name`
- `short_name` when available
- `custom_emoji_id` for Serie A where available
- `crest_url` for external teams where available
- `country_code` for external teams where available

External response additionally includes:

- `competition`: `ucl | uel | uecl | coppa_italia`
- `stage_key`
- `stage_label`
- `stage_order`
- `round_number` when present

Serie A response uses `competition: serie_a` and can retain its round metadata.

## Match status normalization

External statuses map to the existing Match Center state model:

- `scheduled` → upcoming
- `live` → live
- `halftime` → live
- `extra_time` → live
- `penalties` → live
- `finished` → finished
- `postponed` → upcoming/postponed presentation
- `cancelled` → non-live cancelled presentation

BSD detail may enrich the display status, but the database status remains the safe fallback.

## Prediction data

### Current user prediction

Serie A:

- read from `cp_predictions` by `(user_id, match_id)`.

External:

- read from `cp_external_predictions` by `(user_id, external_match_id)`.

### Prediction split

The aggregate home/draw/away split follows the existing Match Center calculation.

For external matches, it uses only `cp_external_predictions` rows for that external match.

No Serie A prediction rows may participate in an external split, even if the numeric IDs overlap.

## BSD data pipeline

The current lazy section model remains:

- `detail`
- `stats`
- `incidents`
- `lineups`
- `player_stats`
- `overview_meta`

For external matches, the BSD event ID is `cp_external_matches.provider_event_id`.

The same BSD routes are used:

- event detail
- stats
- incidents
- lineups
- player stats

`overview_meta` may still include venue, referee and recent team form from BSD. It must not assume that either team exists in `cp_teams`.

## Cache design

Existing `cp_match_center_cache` has a foreign key to `cp_matches`, so external matches must not be inserted there.

Create:

`cp_external_match_center_cache`

Columns mirror the useful fields of the existing cache:

- `external_match_id bigint primary key references cp_external_matches(id) on delete cascade`
- `provider_event_id bigint not null`
- `status text nullable`
- `payload jsonb not null default '{}'::jsonb`
- `fetched_at timestamptz not null default now()`

The same cache-refresh strategy and section-level payload metadata are used.

Cache key space is physically isolated by table, eliminating numeric-ID collisions.

## Polling and freshness

Reuse current Match Center behavior:

- live: frequent summary refresh;
- upcoming: slower polling;
- finished: long-lived cached sections;
- lineups can stay cached once confirmed;
- unavailable BSD sections fail independently.

Existing frontend live refresh must pass `matchViewSource` on every summary or section request.

## Frontend state and navigation

Add `matchViewSource`, default `serie_a` for all legacy internal entry points.

### Open contract

Conceptually:

```text
openMatchCenter(id, source = 'serie_a')
```

External entry points call:

```text
openMatchCenter(externalMatchId, 'external')
```

### Return state

Persist and restore:

- `matchViewSource`
- `matchViewId`
- `matchCenterTab`
- originating app tab
- current competition in Predictions/Matches
- current stage / round selector
- scroll position

Closing Match Center returns to exactly the prior list state instead of reconstructing a default tournament screen.

## External card behavior

External match cards get an explicit external Match Center locator, e.g. data attributes equivalent to:

- external match ID
- `source=external`

### Predictions event guard

Opening logic ignores interactions originating from:

- `.cw29-score-pick`
- the score picker overlay
- buttons
- tournament/stage controls
- any prediction action control

Only a click/tap on free card space opens Match Center.

The existing rule that club profiles are disabled inside Predictions remains unchanged.

## Frontend team presentation

Team logo renderer becomes source-aware:

1. if `crest_url` exists, render external crest;
2. else if `custom_emoji_id` exists, use the existing Telegram emoji asset path;
3. else use the football fallback.

External crests should use fixed dimensions and `object-fit: contain` to avoid layout jumping.

## Match Center hero

### Serie A

Keep existing round/date presentation.

### External

Hero metadata uses:

`<Tournament Label> · <Stage Label>`

Examples:

- `Лига чемпионов · Общий этап`
- `Лига Европы · Общий этап`
- `Лига конференций · Общий этап`
- `Кубок Италии · 1/8 финала`

The hero also shows:

- status / LIVE state;
- team crests and names;
- score;
- kickoff time;
- current user's prediction when present;
- awarded points when calculated.

## Serie A context rule

`__cw18MatchContext` or its successor renders only when:

```text
match source == serie_a
```

For `source=external`, the component returns an empty string and no Serie A table lookup, scorer lookup, or local club context prefetch should be required to render Match Center.

This is a hard product rule, not merely a CSS hide.

## Graceful degradation

A missing optional BSD dataset must not break the screen.

Examples:

- no shotmap → omit shotmap section;
- no momentum → omit momentum section;
- no lineups → show the existing empty state;
- no player stats → show the existing empty state;
- no weather → omit weather details;
- temporary BSD section failure → preserve cached payload and expose a local section error without replacing the whole Match Center.

If the external match itself cannot be resolved, return a normal 404-style Match Center error rather than falling back to a Serie A match with the same numeric ID.

## Compatibility constraints

The implementation must not change:

- Serie A prediction save/autosave behavior;
- `cw29` score picker behavior;
- Predictions club-profile navigation rule;
- existing Serie A Match Center behavior except for carrying explicit source internally;
- existing Rating feature work;
- existing Home favorite-club logic.

## Testing strategy

### Backend RED contracts

Before implementation, prove:

1. current summary endpoint cannot resolve `{source:'external', match_id:<real external id>}`;
2. current full endpoint cannot resolve the same external match;
3. current cache schema cannot safely store external IDs in `cp_match_center_cache`.

### Backend GREEN contracts

Verify:

- one real UCL match;
- one real UEL match;
- one real UECL match;
- one real Coppa Italia match;
- source collision case where internal and external numeric IDs are equal;
- current-user external prediction comes from `cp_external_predictions`;
- external prediction split comes only from `cp_external_predictions`;
- Serie A request still returns the original internal match.

### Frontend contracts

Verify:

- external card opens Match Center from Matches;
- external card opens Match Center from Predictions;
- tapping `cw29` score digit opens score picker and does not open Match Center;
- picker selection still autosaves;
- Match Center theme matches competition;
- external Match Center contains no “Контекст Серии А”;
- Serie A Match Center still contains its Serie A context when data is available;
- back navigation restores tournament/stage/scroll;
- session restore preserves source;
- live refresh uses source;
- lazy tab loading uses source;
- `node --check` succeeds for all inline JavaScript;
- production tree cleanup is performed after the feature is visually accepted.

## Rollout

1. Create database cache table through a migration.
2. Extend/deploy summary backend.
3. Extend/deploy full Match Center backend.
4. Smoke-test all four external competitions at backend level.
5. Add source-aware frontend Match Center requests and state.
6. Add external card entry points with prediction-control event guards.
7. Add tournament themes and external hero metadata.
8. Verify Serie A regression contracts and `cw29` picker.
9. Deploy GitHub Pages.
10. User validates screenshots / navigation in Telegram Mini App.
11. Remove temporary implementation workflows/spec tooling when the feature is accepted, restoring the intended production repository shape.

## Out of scope

- redesigning Serie A Match Center beyond source plumbing;
- building club profiles for every external club;
- changing prediction scoring;
- adding new external competitions;
- changing external match ingestion/sync logic;
- fixing unrelated Rating rank inconsistency in this task;
- changing RLS on unrelated `qptg_*` tables.
