# Ciao, Web! — Tournament Tables & Coppa Italia Bracket

Date: 2026-09-09
Status: approved design
Production invariant: `main` must remain index-only. This spec lives on a design branch and must not be merged into `main`.

## Goal

Extend the existing `Таблицы` section so it becomes a tournament hub for five competitions:

- Serie A — keep the existing table and live behavior.
- UEFA Champions League — full 36-team league-phase table.
- UEFA Europa League — full 36-team league-phase table.
- UEFA Conference League — full 36-team league-phase table.
- Coppa Italia — full premium knockout bracket from Round of 32 (`1/16`) through the final.

The new screens must look native to each competition, keep the existing premium Ciao, Web! language, preserve current Predictions/Matches flows, and work well inside the Telegram Mini App on mobile.

## User-facing behavior

### Tables hub

Opening `Таблицы` shows five premium tournament cards in the same family as the existing Matches and Predictions tournament hubs.

Themes:

- Serie A: deep blue / electric blue.
- Champions League: midnight navy / violet / cool star-like glow.
- Europa League: near-black / orange / warm metallic glow.
- Conference League: dark emerald / green.
- Coppa Italia: dark premium base with restrained Italian green / white / red accents.

Tournament selection changes the background/theme while keeping the global navigation unchanged.

### UEFA league-phase tables

For `ucl`, `uel`, and `uecl`, render all 36 clubs, not only clubs already present in `cp_external_matches`.

Primary mobile columns:

`# · Команда · И · РМ · О`

Each row may additionally expose compact secondary data (`В–Н–П`, goals) without widening the table beyond the Mini App viewport.

Qualification zones:

- positions 1–8: direct qualification to Round of 16;
- positions 9–24: knockout phase play-offs;
- positions 25–36: eliminated.

Zone changes are communicated with a thin left accent / subtle row tint and a compact legend. The table must not become a rainbow block.

Italian clubs are visually distinguished slightly. A team row/name is interactive only when the provider row is Italian and resolves to an existing local Ciao profile through `cp_teams.bsd_team_id -> cp_teams.id`. Foreign clubs are informational only and must not appear clickable.

### Coppa Italia bracket

Render the complete knockout path:

`1/16 -> 1/8 -> 1/4 -> 1/2 -> Финал`

Round of 32 contains 16 match slots. Later rounds contain 8, 4, 2, and 1 respectively.

Mobile interaction is a horizontal swipe/scroll bracket with round snapping. Each round is a vertical column of match cards; connector lines visually communicate progression where layout allows it without harming readability. The current/nearest active stage should be the initial scroll target.

Each match card shows:

- team crests;
- team names;
- score when live or finished;
- compact status / minute;
- kickoff date/time for scheduled matches;
- winner emphasis after completion.

Future slots whose participant is not known yet use a premium placeholder rather than fabricated team data.

Every actual Coppa Italia match card is clickable and opens the existing full external Match Center. Team-profile links remain separate from match-card navigation and are enabled only when a local profile mapping exists.

## Architecture

### Frontend

Production remains a single root `index.html`.

Add a new `Tables` controller layer inside `index.html` rather than changing the global tab model. The existing `tab==='seriea'` entry becomes the tournament-tables entry point while preserving the current Serie A renderer as one child competition.

Recommended frontend state:

- `__cwTblCompetition`: `'' | serie_a | ucl | uel | uecl | coppa_italia`
- `__cwTblPayload`: current standings or bracket payload
- `__cwTblLoading`
- `__cwTblError`
- `__cwTblLoadedAt`
- request/version guard to ignore stale responses

No changes to `cw29` prediction picker, Predictions APIs, external match navigation, live polling scheduler, or rating logic.

### New backend API

Create a dedicated Supabase Edge Function:

`ciao-tournament-tables-v1`

It is the only data source used by the new frontend screens. The browser must not call the upstream provider directly.

The function uses the same Telegram Mini App custom-auth pattern as existing Ciao APIs (`verify_jwt=false` at platform level, Telegram init-data validation inside the function).

Supported actions:

#### `standings`

Input:

```json
{"action":"standings","competition":"ucl"}
```

Allowed competitions: `ucl`, `uel`, `uecl`.

Response shape:

```json
{
  "ok": true,
  "competition": "ucl",
  "season": "2026/27",
  "stale": false,
  "updated_at": "ISO timestamp",
  "rows": [
    {
      "position": 1,
      "provider_team_id": 123,
      "local_team_id": 7,
      "name": "Club",
      "short_name": "Club",
      "country_code": "ITA",
      "crest_url": "https://...",
      "played": 8,
      "won": 6,
      "drawn": 1,
      "lost": 1,
      "goals_for": 18,
      "goals_against": 7,
      "goal_difference": 11,
      "points": 19,
      "zone": "direct"
    }
  ]
}
```

`zone` is one of `direct`, `playoff`, `eliminated` and is determined from the returned official position.

`local_team_id` is populated only by matching provider/BSD team ID against `cp_teams.bsd_team_id`. This keeps foreign clubs non-clickable and avoids frontend hard-coded mapping as the source of truth.

The provider adapter must fetch the provider's complete official standings view for the competition. It must not derive a UEFA 36-team table from the current `cp_external_matches`, because that table intentionally contains only prediction/match-center coverage and is not a complete competition dataset.

### `bracket`

Input:

```json
{"action":"bracket","competition":"coppa_italia"}
```

Response shape:

```json
{
  "ok": true,
  "competition": "coppa_italia",
  "season": "2026/27",
  "stale": false,
  "updated_at": "ISO timestamp",
  "rounds": [
    {
      "key": "r32",
      "label": "1/16",
      "order": 300,
      "matches": [
        {
          "external_match_id": 42,
          "provider_event_id": 601024,
          "kickoff_at": "ISO timestamp",
          "status": "scheduled|live|finished|postponed|cancelled",
          "minute": 60,
          "home": {"provider_team_id":1,"local_team_id":7,"name":"Club A","crest_url":"..."},
          "away": {"provider_team_id":2,"local_team_id":null,"name":"Club B","crest_url":"..."},
          "home_score": 2,
          "away_score": 1,
          "winner_side": "home|away|null"
        }
      ]
    }
  ]
}
```

Round keys are normalized to `r32`, `r16`, `qf`, `sf`, `final`.

The provider adapter must fetch the complete Coppa Italia competition match set, not the currently partial rows already stored for predictions. Every real match returned by the full provider feed is upserted into `cp_external_matches` using the existing unique identity `(competition, provider_event_id)`. The API then returns the resulting numeric `cp_external_matches.id` as `external_match_id` so the frontend can open the existing external Match Center for every bracket match without introducing a second Match Center identity scheme.

Advancement shown in the UI is based on the official provider bracket/match stage data. The frontend may visually infer a winner from a finished score, but it must not invent the participant of a future match when the provider has not yet supplied that participant.

## Cache and resilience

Add one generic cache table for rendered competition views:

`cp_competition_views_cache`

Logical key: `(season, competition, view_type)` where `view_type` is `standings` or `bracket`.

Stored fields:

- `season`
- `competition`
- `view_type`
- `payload jsonb`
- `provider_updated_at`
- `fetched_at`
- `expires_at`

Refresh policy:

- standings during a live match window: target freshness 30 seconds;
- standings outside live windows: 5 minutes;
- Coppa bracket during a live match window: target freshness 15 seconds;
- Coppa bracket outside live windows: 5 minutes;
- finished historical stages may be reused from cache until provider data changes.

On provider failure, return the last valid cache snapshot with `stale:true`. If no cache exists, return a typed `provider_unavailable` error. Never replace a previously valid table/bracket with an empty provider response unless the response is explicitly authoritative.

## Styling details

Use CSS custom properties per table theme so the same components can be reused:

- accent
- accent RGB
- secondary accent
- surface top/bottom
- glow
- zone colors

Do not embed official UEFA/Coppa artwork unless an existing legally usable asset source already supplies it. Tournament identity should come from palette, typography, light effects, borders, and restrained abstract motifs.

The 36-row tables must remain vertically scrollable inside the app with no horizontal page scroll. Team names truncate gracefully only as a last resort; the team column gets the flexible width.

The Coppa bracket may scroll horizontally inside its own container, with `scroll-snap-type:x mandatory`; the global app shell must not horizontally scroll.

The shared Italian premium loading system is used while standings/bracket data is loading.

## Navigation

- Tables hub -> competition screen: internal state transition, no page reload.
- Competition screen -> hub: back button restores the hub and its scroll state.
- Italian UEFA team -> existing club profile using `local_team_id`.
- Foreign UEFA team -> no click handler and no link affordance.
- Coppa match card -> existing external Match Center using numeric `external_match_id`.
- Coppa team name/crest -> club profile only if `local_team_id` exists; clicking the team control must stop propagation so it does not also open the match.

## Error handling

Each tournament screen distinguishes:

- loading;
- stale but usable data;
- provider error with cached data;
- provider error without data;
- empty/unsupported competition response.

A stale badge is subtle (`Данные могут быть неактуальны`) and does not block interaction.

## Testing and verification

Backend tests/contracts:

- standings accepts only `ucl`, `uel`, `uecl`;
- each valid UEFA response contains exactly 36 unique positions when the provider season is in league phase;
- zone mapping: 1–8 direct, 9–24 playoff, 25–36 eliminated;
- local team mapping comes from `cp_teams.bsd_team_id`;
- bracket normalizes stages in order `r32,r16,qf,sf,final`;
- full r32 supports 16 matches;
- all bracket matches returned with provider IDs are upserted into `cp_external_matches` and expose numeric `external_match_id`;
- stale-cache fallback works and never overwrites good cache with accidental empty data.

Frontend tests/contracts:

- Tables hub has five tournament cards;
- Serie A existing renderer remains available;
- UEFA table renders 36 rows and no horizontal page overflow;
- only rows with Italian/local profile mapping expose club-profile navigation;
- Coppa renders five stages and bracket-local horizontal scrolling;
- every real Coppa match with `external_match_id` opens Match Center;
- participant placeholders do not open Match Center;
- Italian premium loader appears during fetch;
- existing `cw29`, external Matches, Predictions and Rating markers remain present;
- all inline scripts pass `node --check`.

Production verification:

- deploy backend first and smoke-check API payloads;
- implement frontend only after backend contracts pass;
- preserve production tree as root `index.html` only;
- verify GitHub Pages deployment success at the final production SHA;
- smoke on narrow mobile width and typical Telegram Mini App width.

## Rollout

1. Create/cache the new backend view API and verify full-provider coverage.
2. Validate 36-row UCL/UEL/UECL responses and complete Coppa stage coverage before touching production UI.
3. Add Tables hub/controller and tournament themes to `index.html`.
4. Wire Italian club profile navigation.
5. Wire all Coppa bracket cards to the existing external Match Center.
6. Run regression checks on Serie A table, Predictions, Matches, Rating, club profile and boot/loading states.
7. Deploy Pages and verify the production tree remains index-only.

## Explicit non-goals

- No foreign club profiles in this change.
- No redesign of Predictions or Matches tournament hubs.
- No new Match Center implementation.
- No manual frontend computation of UEFA tiebreak rules.
- No replacement of the existing Serie A table backend.
- No modification of rating/scoring rules.
