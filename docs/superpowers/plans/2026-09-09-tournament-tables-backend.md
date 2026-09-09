# Tournament Tables Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to execute this plan task-by-task. Follow RED → GREEN → verification for every behavior change.

**Goal:** Build `ciao-tournament-tables-v1`, an authenticated Supabase Edge Function that serves complete 36-club UEFA league-phase standings and a complete Coppa Italia knockout view with stale-cache fallback and existing external Match Center IDs.

**Architecture:** Backend source/tests/migration live only on an implementation branch. Production `main` remains index-only. For every competition, discover current BSD `league_id` and `season_id` from an existing `cp_external_matches.provider_event_id` through `/events/{id}/`; never hard-code season IDs and never derive UEFA standings from the intentionally partial prediction match set. Cache normalized competition views in Postgres. For Coppa, upsert every provider event returned by the full competition feed into `cp_external_matches` so each real bracket card has a numeric `external_match_id` compatible with the existing Match Center.

**Tech stack:** Supabase Edge Functions (Deno/TypeScript), plain ES modules, `node:test`, Supabase Postgres, BSD Sports API v2, existing Telegram Mini App custom auth.

**Spec:** `docs/superpowers/specs/2026-09-09-tournament-tables-design.md`

## Non-negotiable contracts

- UEFA `ucl`, `uel`, `uecl`: exactly 36 unique official positions when league phase is available.
- Zones: `1–8 direct`, `9–24 playoff`, `25–36 eliminated`.
- `local_team_id` comes only from `cp_teams.bsd_team_id`.
- Coppa rounds are normalized to `r32`, `r16`, `qf`, `sf`, `final`.
- Real Coppa events retain provider event identity and expose numeric `cp_external_matches.id` as `external_match_id`.
- Unknown future participants are never invented.
- Good cached data is never overwritten by an empty/incomplete provider response.
- Provider failure returns last-good payload with `stale:true`; no-cache failure returns typed `provider_unavailable`.
- `verify_jwt=false` is allowed only because the function enforces existing Telegram init-data validation + `@CiaoCalcio` membership internally.
- No changes to scoring, rating, live scheduler, Predictions, or Match Center functions.

---

## Task 1 — Cache schema

**Files**
- Create: `work/tournament-tables/backend/migrations/20260909_competition_views_cache.sql`
- Create: `work/tournament-tables/backend/tests/schema-contract.test.mjs`

- [ ] **RED:** create a test that reads the migration and requires table `public.cp_competition_views_cache`, PK `(season, competition, view_type)`, `payload jsonb`, `provider_updated_at`, `fetched_at`, `expires_at`, and RLS.

Run:

```bash
node --test work/tournament-tables/backend/tests/schema-contract.test.mjs
```

Expected: FAIL because migration is absent.

- [ ] **GREEN:** create migration:

```sql
create table if not exists public.cp_competition_views_cache (
  season text not null,
  competition text not null check (competition in ('ucl','uel','uecl','coppa_italia')),
  view_type text not null check (view_type in ('standings','bracket')),
  payload jsonb not null,
  provider_updated_at timestamptz,
  fetched_at timestamptz not null default now(),
  expires_at timestamptz not null,
  primary key (season, competition, view_type)
);
create index if not exists cp_competition_views_cache_expires_idx
  on public.cp_competition_views_cache (expires_at);
alter table public.cp_competition_views_cache enable row level security;
```

Apply with `Supabase.apply_migration`, migration name `competition_views_cache`.

- [ ] **Verify:** rerun the test; query `information_schema`/catalog metadata and confirm PK order and RLS.

- [ ] Commit:

```bash
git add work/tournament-tables/backend/migrations work/tournament-tables/backend/tests/schema-contract.test.mjs
git commit -m "test: define tournament view cache contract"
```

---

## Task 2 — UEFA provider metadata and 36-row normalization

**Files**
- Create: `work/tournament-tables/backend/domain.mjs`
- Create: `work/tournament-tables/backend/provider.mjs`
- Create: `work/tournament-tables/backend/tests/domain.test.mjs`
- Create: `work/tournament-tables/backend/tests/provider.test.mjs`

**Exports**

```text
zoneForPosition(position)
normalizeStandings({standingsPayload,teamsPayload,localTeams})
discoverCompetitionMeta({competition,findSeedEvent,bsd})
fetchUefaView({competition,findSeedEvent,bsd,localTeams})
```

- [ ] **RED:** domain tests assert boundary positions 1/8/9/24/25/36 and a provider team `bsd_team_id=77` maps to local Ciao team ID while a foreign provider ID maps to `null`.

- [ ] Implement `zoneForPosition` and `normalizeStandings`. Required normalized row shape:

```js
{
  position, provider_team_id, local_team_id,
  name, short_name, country_code, crest_url,
  played, won, drawn, lost,
  goals_for, goals_against, goal_difference, points,
  zone
}
```

Use tolerant field aliases for provider values, but output only this canonical shape.

- [ ] **RED:** provider tests assert metadata discovery calls `/events/{seedEvent}/` and extracts `league_id` + `season_id`; official standings request is `/leagues/{leagueId}/standings/?season_id={seasonId}` and teams request is `/teams/?league_id={leagueId}&season_id={seasonId}&limit=100`.

- [ ] Implement dynamic discovery:

```js
export async function discoverCompetitionMeta({competition,findSeedEvent,bsd}){
  if(!['ucl','uel','uecl','coppa_italia'].includes(String(competition))) throw new Error('invalid_competition');
  const seedEventId=Number(await findSeedEvent(competition));
  if(!Number.isSafeInteger(seedEventId)||seedEventId<=0) throw new Error('competition_seed_missing');
  const detail=await bsd(`/events/${seedEventId}/`);
  const leagueId=Number(detail?.league_id),seasonId=Number(detail?.season_id);
  if(!Number.isSafeInteger(leagueId)||!Number.isSafeInteger(seasonId)) throw new Error('competition_meta_missing');
  return {competition:String(competition),seedEventId,leagueId,seasonId};
}
```

- [ ] Implement `fetchUefaView(...)`, fetch standings + teams in parallel, normalize, then reject as `standings_incomplete` unless there are exactly 36 rows with unique positions 1..36.

Provider facts already observed and useful only as smoke references, not hard-coded configuration:

```text
UCL seed 601024 -> league 7 / season 1112
UEL seed 601173 -> league 8 / season 1269
UECL seed 601326 -> league 83 / season 1606
```

- [ ] Verify:

```bash
node --test work/tournament-tables/backend/tests/domain.test.mjs work/tournament-tables/backend/tests/provider.test.mjs
```

- [ ] Commit:

```bash
git add work/tournament-tables/backend
git commit -m "feat: normalize official UEFA standings"
```

---

## Task 3 — Complete Coppa event normalization

**Files**
- Modify: `work/tournament-tables/backend/domain.mjs`
- Modify: `work/tournament-tables/backend/provider.mjs`
- Create: `work/tournament-tables/backend/tests/coppa.test.mjs`

**Exports**

```text
coppaStageKey(event)
normalizeCoppaEvent(event, localTeamMap)
fetchCoppaEvents({findSeedEvent,bsd,localTeams})
```

- [ ] **RED:** stage tests cover `Round of 32 -> r32`, `Round of 16/1/8 -> r16`, quarter-final -> `qf`, semi-final -> `sf`, final -> `final`, and preliminary/unknown -> `null`.

- [ ] Implement `coppaStageKey(event)` using `stage`, `stage_name`, `round_label`, and `round_name` aliases. Match `semi` before generic `final` so `Semi-finals` cannot be misclassified.

- [ ] Implement `normalizeCoppaEvent(event, localTeamMap)`. Canonical actual-event shape:

```js
{
  stage_key,
  provider_event_id,
  kickoff_at,
  status,
  minute,
  home:{provider_team_id,local_team_id,name,crest_url},
  away:{provider_team_id,local_team_id,name,crest_url},
  home_score,
  away_score,
  winner_side,
  previous_leg_event_id
}
```

Do not create a row when there is no valid provider event ID or no recognized bracket stage.

- [ ] **RED:** pagination test uses a fake seed detail with league/season metadata and verifies offsets `0` and `200` when provider `count` exceeds one page. Include preliminary events and events from another league; they must be filtered out.

- [ ] Implement `fetchCoppaEvents({findSeedEvent,bsd,localTeams})`:
  1. discover Coppa league + season through seed event;
  2. page `/events/?season_id={seasonId}&limit=200&offset={offset}` up to provider count;
  3. retain only `event.league_id===meta.leagueId`;
  4. build `localTeamMap = new Map(localTeams.filter(x=>x.bsd_team_id).map(x=>[Number(x.bsd_team_id),x]))`;
  5. normalize each event with `normalizeCoppaEvent(event, localTeamMap)`;
  6. require at least one actual `r32` event, otherwise throw `coppa_r32_missing`.

The localization contract ends here: `fetchCoppaEvents` already returns events with `local_team_id`. There is **no** separate `localizeCoppaEvent` function.

- [ ] Verify:

```bash
node --test work/tournament-tables/backend/tests/coppa.test.mjs work/tournament-tables/backend/tests/domain.test.mjs work/tournament-tables/backend/tests/provider.test.mjs
```

- [ ] Commit:

```bash
git add work/tournament-tables/backend
git commit -m "feat: normalize complete Coppa bracket events"
```

---

## Task 4 — Cache service and external Match Center identities

**Files**
- Create: `work/tournament-tables/backend/service.mjs`
- Create: `work/tournament-tables/backend/tests/service.test.mjs`

**Repository contract**

```text
findSeedEvent(competition)
localTeams()
readCache(season,competition,viewType)
writeCache(row)
upsertExternalMatches(events) -> Map<provider_event_id, cp_external_matches.id>
```

**Service export**

```text
createTournamentTablesService({repository,provider,now})
  .standings(competition)
  .bracket()
```

- [ ] **RED:** stale-cache test: expired good cache + provider failure returns cached payload with `stale:true`.

- [ ] **RED:** empty/incomplete provider response test: existing 36-row cache must remain untouched (`writeCache` call count stays zero) and is returned stale.

- [ ] Implement season helper from UTC date (`2026/27` style) and cache TTL policy:

```js
const TTL={
  standings:{live:30_000,idle:300_000},
  bracket:{live:15_000,idle:300_000}
};
```

A cache row is fresh only when `Date.parse(expires_at)>now()`. A UEFA payload is valid only for exactly 36 unique positions. A Coppa payload is valid only if it contains at least one actual `r32` event.

- [ ] **RED:** Coppa identity test: fake provider events `7001`, `7002`, repository returns `Map([[7001,41],[7002,42]])`; service result must contain `external_match_id:41/42` on the corresponding actual events.

- [ ] Implement Coppa service flow exactly through the already-localized provider interface:

```js
const localTeams=await repository.localTeams();
const raw=await provider.fetchCoppaEvents({
  findSeedEvent:repository.findSeedEvent,
  bsd:provider.bsd,
  localTeams
});
const idMap=await repository.upsertExternalMatches(raw.events);
const withIds=raw.events.map(e=>({
  ...e,
  external_match_id:idMap.get(Number(e.provider_event_id))??null
}));
```

Group actual events into fixed output round order:

```text
r32 -> 1/16
r16 -> 1/8
qf  -> 1/4
sf  -> 1/2
final -> Финал
```

Never fabricate an `external_match_id`; unknown future slots are a frontend concern.

- [ ] Implement cache write only after validation and Match Center ID mapping succeeds. Cache payload stores canonical response content, not raw provider JSON.

- [ ] Verify:

```bash
node --test work/tournament-tables/backend/tests/*.test.mjs
```

- [ ] Commit:

```bash
git add work/tournament-tables/backend
git commit -m "feat: add tournament table cache service"
```

---

## Task 5 — HTTP Edge Function, deploy, real-provider smoke

**Files**
- Create: `work/tournament-tables/backend/index.ts`
- Create: `work/tournament-tables/backend/auth.mjs`
- Create: `work/tournament-tables/backend/tests/http-contract.test.mjs`

**HTTP contract**

```text
GET -> service metadata
POST {action:'standings',competition:'ucl|uel|uecl'}
POST {action:'bracket',competition:'coppa_italia'}
```

- [ ] Structure request dispatch so `handleRequest(req,deps)` is testable independently from final `Deno.serve(...)`.

- [ ] **RED:** HTTP tests require invalid action/competition pairs to return 400, auth failure to return 401/403, and provider/service methods not to execute before auth succeeds.

- [ ] Implement focused `auth.mjs` from the proven Ciao custom-auth behavior:
  - validate Telegram WebApp signature and max auth age;
  - resolve/create `cp_users` user;
  - require `@CiaoCalcio` member/admin/creator;
  - cache membership briefly as existing Ciao functions do.

- [ ] Implement production repository:

```js
findSeedEvent: async competition => {
  const q=await db.from('cp_external_matches')
    .select('provider_event_id')
    .eq('competition',competition)
    .order('kickoff_at',{ascending:true})
    .limit(1)
    .maybeSingle();
  if(q.error)throw q.error;
  return q.data?.provider_event_id??null;
},
localTeams: async()=>{
  const q=await db.from('cp_teams')
    .select('id,name,short_name,custom_emoji_id,bsd_team_id')
    .not('bsd_team_id','is',null);
  if(q.error)throw q.error;
  return q.data??[];
}
```

Repository `readCache`/`writeCache` uses `cp_competition_views_cache` only via service-role access inside the Edge Function.

- [ ] Implement `upsertExternalMatches(events)` using existing `cp_external_matches` schema and unique key `(competition,provider_event_id)`. For each Coppa actual event write:
  - `competition='coppa_italia'`, `provider='bsd'`;
  - provider event ID;
  - canonical `stage_key`, `stage_label`, `stage_order` (`r32=300,r16=400,qf=500,sf=600,final=700`);
  - kickoff/status/minute;
  - home/away BSD IDs, names, crest URLs;
  - scores/provider timestamps.
  Then `.select('id,provider_event_id')` and return a `Map`.

- [ ] Implement typed errors:

```text
invalid_competition -> 400
competition_seed_missing -> 503
provider_unavailable -> 503 when no cache exists
subscription_required -> 403
invalid/expired Telegram auth -> 401
```

GET metadata:

```json
{"ok":true,"service":"ciao-tournament-tables-v1","version":1,"competitions":["ucl","uel","uecl","coppa_italia"]}
```

- [ ] Verify all backend tests:

```bash
node --test work/tournament-tables/backend/tests/*.test.mjs
```

- [ ] Deploy exactly `index.ts`, `auth.mjs`, `domain.mjs`, `provider.mjs`, `service.mjs` as `ciao-tournament-tables-v1` with `verify_jwt=false` because custom Telegram auth is enforced inside `handleRequest`.

- [ ] Real-provider smoke **before frontend changes** using a valid Mini App auth request:

```text
UCL: rows.length === 36; unique positions === 36
UEL: rows.length === 36; unique positions === 36
UECL: rows.length === 36; unique positions === 36
Coppa: rounds include r32; every actual returned event has external_match_id > 0
```

Also query `cp_external_matches` and confirm no duplicate `(competition,provider_event_id)` rows for Coppa.

- [ ] Cache smoke: after a successful request, a second request can be served from `cp_competition_views_cache`; unit tests cover provider failure without modifying real credentials.

- [ ] Commit backend implementation source on the implementation branch:

```bash
git add work/tournament-tables/backend
git commit -m "feat: deploy tournament tables API"
```

**Do not merge backend source, tests, migrations, specs, or plans into production `main`.** They remain on the implementation/design branch as auditable source; production `main` receives only the verified final `index.html` during frontend rollout.
