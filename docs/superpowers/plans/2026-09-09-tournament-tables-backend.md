# Tournament Tables Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `ciao-tournament-tables-v1`, a dedicated authenticated Supabase Edge Function that serves full UEFA 36-team standings and a complete Coppa Italia bracket with stale-cache fallback and existing Match Center identities.

**Architecture:** Keep the production `main` branch index-only. Backend source, tests, and migration live only on an implementation branch/worktree and are deployed to Supabase from there. The service discovers provider `league_id`/`season_id` from an existing `cp_external_matches.provider_event_id` via BSD `/events/{id}/`, then uses BSD official standings/teams/event endpoints; it never derives UEFA standings from the partial prediction match set.

**Tech Stack:** Supabase Edge Functions (Deno/TypeScript), plain ES modules, `node:test` for pure-module tests, Supabase Postgres, BSD Sports API v2, existing Telegram Mini App custom authentication pattern.

**Spec:** `docs/superpowers/specs/2026-09-09-tournament-tables-design.md`

## Global Constraints

- Production `main` must remain root `index.html` only.
- UEFA screens must return full official 36-team tables for `ucl`, `uel`, `uecl`.
- Qualification zones are exactly `1–8 direct`, `9–24 playoff`, `25–36 eliminated`.
- `local_team_id` comes only from `cp_teams.bsd_team_id` mapping; foreign clubs remain non-clickable in the frontend.
- Coppa Italia must cover `r32`, `r16`, `qf`, `sf`, `final` and every real event must map to a numeric `cp_external_matches.id` for the existing external Match Center.
- Provider failure returns the latest valid cache snapshot with `stale:true`; an accidental empty provider payload must never overwrite good cache.
- Platform JWT verification remains disabled only because the function performs the same Telegram init-data + channel-membership custom auth already used by Ciao APIs.
- No changes to prediction scoring, rating, live scheduler, or existing Match Center functions.

---

### Task 1: Create the cache schema and isolated backend workspace

**Files:**
- Create on implementation branch only: `work/tournament-tables/backend/migrations/20260909_competition_views_cache.sql`
- Create: `work/tournament-tables/backend/tests/schema-contract.test.mjs`

**Interfaces:**
- Consumes: existing Supabase project `dkefzepiiudehhzbbrjn`.
- Produces: Postgres table `cp_competition_views_cache` keyed by `(season, competition, view_type)`.

- [ ] **Step 1: Write the failing schema contract test**

```js
// work/tournament-tables/backend/tests/schema-contract.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const sql = fs.readFileSync(new URL('../migrations/20260909_competition_views_cache.sql', import.meta.url), 'utf8');

test('cache migration defines the exact competition-view contract', () => {
  assert.match(sql, /create table if not exists public\.cp_competition_views_cache/i);
  assert.match(sql, /primary key\s*\(season,\s*competition,\s*view_type\)/i);
  for (const col of ['payload jsonb', 'provider_updated_at timestamptz', 'fetched_at timestamptz', 'expires_at timestamptz']) {
    assert.match(sql.toLowerCase(), new RegExp(col.replace(/\s+/g, '\\s+')));
  }
  assert.match(sql, /enable row level security/i);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
node --test work/tournament-tables/backend/tests/schema-contract.test.mjs
```

Expected: FAIL because the migration file does not exist.

- [ ] **Step 3: Write the migration**

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

Apply this SQL using the Supabase migration tool, not ad-hoc DDL through `execute_sql`.

- [ ] **Step 4: Verify the migration and test**

Run:

```bash
node --test work/tournament-tables/backend/tests/schema-contract.test.mjs
```

Then query Supabase metadata and verify the primary key columns are exactly `season, competition, view_type` and RLS is enabled.

Expected: PASS and one cache table.

- [ ] **Step 5: Commit the isolated backend setup**

```bash
git add work/tournament-tables/backend/migrations work/tournament-tables/backend/tests/schema-contract.test.mjs
git commit -m "test: define tournament view cache contract"
```

---

### Task 2: Implement provider metadata discovery and UEFA normalization

**Files:**
- Create: `work/tournament-tables/backend/domain.mjs`
- Create: `work/tournament-tables/backend/provider.mjs`
- Create: `work/tournament-tables/backend/tests/domain.test.mjs`
- Create: `work/tournament-tables/backend/tests/provider.test.mjs`

**Interfaces:**
- Consumes: repository method `findSeedEvent(competition): Promise<number|null>` and BSD fetch function `bsd(path): Promise<object>`.
- Produces:
  - `zoneForPosition(position): 'direct'|'playoff'|'eliminated'`
  - `discoverCompetitionMeta({competition, findSeedEvent, bsd}): Promise<{competition,seedEventId,leagueId,seasonId}>`
  - `normalizeStandings({standingsPayload, teamsPayload, localTeams}): StandingRow[]`
  - `fetchUefaView({competition, findSeedEvent, bsd, localTeams}): Promise<{meta,rows}>`

- [ ] **Step 1: Write failing domain tests**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { zoneForPosition, normalizeStandings } from '../domain.mjs';

test('UEFA zones are 1-8 direct, 9-24 playoff, 25-36 eliminated', () => {
  assert.equal(zoneForPosition(1), 'direct');
  assert.equal(zoneForPosition(8), 'direct');
  assert.equal(zoneForPosition(9), 'playoff');
  assert.equal(zoneForPosition(24), 'playoff');
  assert.equal(zoneForPosition(25), 'eliminated');
  assert.equal(zoneForPosition(36), 'eliminated');
});

test('standings normalization joins provider team and local Ciao mapping', () => {
  const rows = normalizeStandings({
    standingsPayload:{standings:[{position:1,team_id:77,played:1,won:1,drawn:0,lost:0,goals_for:2,goals_against:1,points:3}]},
    teamsPayload:{results:[{id:77,name:'Inter',short_name:'Inter',country:'ITA',crest_url:'https://crest/inter.png'}]},
    localTeams:[{id:11,bsd_team_id:77,name:'Интер'}]
  });
  assert.deepEqual(rows[0], {
    position:1,provider_team_id:77,local_team_id:11,name:'Inter',short_name:'Inter',country_code:'ITA',crest_url:'https://crest/inter.png',
    played:1,won:1,drawn:0,lost:0,goals_for:2,goals_against:1,goal_difference:1,points:3,zone:'direct'
  });
});
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
node --test work/tournament-tables/backend/tests/domain.test.mjs
```

Expected: FAIL because `domain.mjs` does not exist.

- [ ] **Step 3: Implement minimal domain normalization**

Implement exact exported functions:

```js
export function zoneForPosition(position){
  const p=Number(position);
  if(p>=1&&p<=8)return 'direct';
  if(p>=9&&p<=24)return 'playoff';
  return 'eliminated';
}

const arr=x=>Array.isArray(x)?x:Array.isArray(x?.results)?x.results:Array.isArray(x?.standings)?x.standings:[];
const num=(...xs)=>{for(const x of xs){const n=Number(x);if(Number.isFinite(n))return n}return 0};
const code=x=>String(x??'').trim().toUpperCase();

export function normalizeStandings({standingsPayload,teamsPayload,localTeams=[]}){
  const teams=new Map(arr(teamsPayload).map(t=>[Number(t.id),t]));
  const locals=new Map(localTeams.filter(t=>Number(t.bsd_team_id)>0).map(t=>[Number(t.bsd_team_id),t]));
  return arr(standingsPayload).map((r,i)=>{
    const providerTeamId=num(r.team_id,r?.team?.id), t=teams.get(providerTeamId)??r.team??{}, local=locals.get(providerTeamId)??null;
    const gf=num(r.goals_for,r.goals_scored,r.gf),ga=num(r.goals_against,r.goals_conceded,r.ga),position=num(r.position,r.rank,i+1);
    return {position,provider_team_id:providerTeamId,local_team_id:local?Number(local.id):null,name:String(t.name??r.team_name??'—'),short_name:String(t.short_name??t.name??r.team_name??'—'),country_code:code(t.country_code??t.country),crest_url:String(t.crest_url??t.logo_url??''),played:num(r.played,r.matches_played,r.matches),won:num(r.won,r.wins),drawn:num(r.drawn,r.draws),lost:num(r.lost,r.losses),goals_for:gf,goals_against:ga,goal_difference:Number.isFinite(Number(r.goal_difference??r.gd))?Number(r.goal_difference??r.gd):gf-ga,points:num(r.points,r.pts),zone:zoneForPosition(position)};
  }).sort((a,b)=>a.position-b.position);
}
```

- [ ] **Step 4: Write provider discovery tests**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { discoverCompetitionMeta, fetchUefaView } from '../provider.mjs';

test('metadata discovery reads league and season from a seed event detail', async () => {
  const calls=[];
  const meta=await discoverCompetitionMeta({competition:'ucl',findSeedEvent:async()=>601024,bsd:async path=>{calls.push(path);return {id:601024,league_id:7,season_id:1112}}});
  assert.deepEqual(meta,{competition:'ucl',seedEventId:601024,leagueId:7,seasonId:1112});
  assert.deepEqual(calls,['/events/601024/']);
});

test('UEFA view fetches official standings plus league teams', async () => {
  const calls=[];
  const bsd=async path=>{calls.push(path);if(path==='/events/601024/')return {league_id:7,season_id:1112};if(path==='/leagues/7/standings/?season_id=1112')return {standings:Array.from({length:36},(_,i)=>({position:i+1,team_id:i+1,played:1,points:36-i}))};if(path==='/teams/?league_id=7&season_id=1112&limit=100')return {results:Array.from({length:36},(_,i)=>({id:i+1,name:`Club ${i+1}`}))};throw new Error(path)};
  const view=await fetchUefaView({competition:'ucl',findSeedEvent:async()=>601024,bsd,localTeams:[]});
  assert.equal(view.rows.length,36);
  assert.equal(new Set(view.rows.map(x=>x.position)).size,36);
  assert.ok(calls.includes('/leagues/7/standings/?season_id=1112'));
});
```

- [ ] **Step 5: Implement provider discovery and UEFA fetch**

```js
import { normalizeStandings } from './domain.mjs';

const UEFA=new Set(['ucl','uel','uecl']);
export async function discoverCompetitionMeta({competition,findSeedEvent,bsd}){
  if(!['ucl','uel','uecl','coppa_italia'].includes(String(competition)))throw new Error('invalid_competition');
  const seedEventId=Number(await findSeedEvent(competition));
  if(!Number.isSafeInteger(seedEventId)||seedEventId<=0)throw new Error('competition_seed_missing');
  const detail=await bsd(`/events/${seedEventId}/`),leagueId=Number(detail?.league_id),seasonId=Number(detail?.season_id);
  if(!Number.isSafeInteger(leagueId)||!Number.isSafeInteger(seasonId))throw new Error('competition_meta_missing');
  return {competition:String(competition),seedEventId,leagueId,seasonId};
}

export async function fetchUefaView({competition,findSeedEvent,bsd,localTeams}){
  if(!UEFA.has(String(competition)))throw new Error('invalid_uefa_competition');
  const meta=await discoverCompetitionMeta({competition,findSeedEvent,bsd});
  const [standingsPayload,teamsPayload]=await Promise.all([
    bsd(`/leagues/${meta.leagueId}/standings/?season_id=${meta.seasonId}`),
    bsd(`/teams/?league_id=${meta.leagueId}&season_id=${meta.seasonId}&limit=100`)
  ]);
  const rows=normalizeStandings({standingsPayload,teamsPayload,localTeams});
  if(rows.length!==36||new Set(rows.map(x=>x.position)).size!==36)throw new Error('standings_incomplete');
  return {meta,rows};
}
```

Provider facts already verified from current Match Center cache: UCL event `601024` reports `league_id=7, season_id=1112`; UEL `601173` reports `league_id=8, season_id=1269`; UECL `601326` reports `league_id=83, season_id=1606`. Discovery remains dynamic so the next season does not require hard-coded IDs.

- [ ] **Step 6: Run provider/domain tests and commit**

Run:

```bash
node --test work/tournament-tables/backend/tests/domain.test.mjs work/tournament-tables/backend/tests/provider.test.mjs
```

Expected: PASS.

```bash
git add work/tournament-tables/backend/domain.mjs work/tournament-tables/backend/provider.mjs work/tournament-tables/backend/tests
git commit -m "feat: normalize official UEFA standings"
```

---

### Task 3: Implement complete Coppa Italia event/bracket normalization

**Files:**
- Modify: `work/tournament-tables/backend/domain.mjs`
- Modify: `work/tournament-tables/backend/provider.mjs`
- Create: `work/tournament-tables/backend/tests/coppa.test.mjs`

**Interfaces:**
- Consumes: `discoverCompetitionMeta(...)`, BSD `/events/?season_id={seasonId}&limit=200&offset={offset}`.
- Produces:
  - `coppaStageKey(event): 'r32'|'r16'|'qf'|'sf'|'final'|null`
  - `fetchCoppaEvents({findSeedEvent,bsd}): Promise<{meta,events}>`
  - normalized actual-event objects preserving `provider_event_id`.

- [ ] **Step 1: Write failing Coppa stage tests**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { coppaStageKey } from '../domain.mjs';

const cases=[
  [{stage_name:'Round of 32'},'r32'],
  [{round_label:'1/8 финала'},'r16'],
  [{stage:'quarter-finals'},'qf'],
  [{stage_name:'Semi-finals'},'sf'],
  [{stage_name:'Final'},'final']
];
for(const [event,key] of cases)test(`maps ${key}`,()=>assert.equal(coppaStageKey(event),key));
```

- [ ] **Step 2: Run RED**

```bash
node --test work/tournament-tables/backend/tests/coppa.test.mjs
```

Expected: FAIL because `coppaStageKey` is missing.

- [ ] **Step 3: Implement stage mapping and event normalization**

Add to `domain.mjs`:

```js
export function coppaStageKey(event){
  const s=[event?.stage,event?.stage_name,event?.round_label,event?.round_name].filter(Boolean).join(' ').toLowerCase();
  if(/semi|1\/2/.test(s))return 'sf';
  if(/quarter|1\/4/.test(s))return 'qf';
  if(/round of 32|1\/16|\br32\b/.test(s))return 'r32';
  if(/round of 16|1\/8|\br16\b/.test(s))return 'r16';
  if(/\bfinal\b/.test(s))return 'final';
  return null;
}

export function normalizeCoppaEvent(event,locals=new Map()){
  const key=coppaStageKey(event);if(!key)return null;
  const team=t=>{const id=Number(t?.id??t?.team_id),local=locals.get(id)??null;return {provider_team_id:id||null,local_team_id:local?Number(local.id):null,name:String(t?.name??'—'),crest_url:String(t?.crest_url??t?.logo_url??'')}};
  const status=String(event?.status??'scheduled').toLowerCase();
  const hs=Number.isInteger(event?.home_score)?event.home_score:null,as=Number.isInteger(event?.away_score)?event.away_score:null;
  return {stage_key:key,provider_event_id:Number(event?.id),kickoff_at:event?.event_date??null,status,minute:Number.isFinite(Number(event?.current_minute))?Number(event.current_minute):null,home:team(event?.home_team),away:team(event?.away_team),home_score:hs,away_score:as,winner_side:status==='finished'&&hs!=null&&as!=null&&hs!==as?(hs>as?'home':'away'):null,previous_leg_event_id:Number(event?.previous_leg_event_id)||null};
}
```

- [ ] **Step 4: Write pagination/filter test**

Test `fetchCoppaEvents` with a fake seed event returning `league_id=9, season_id=1400`; fake page 1 contains R32 + preliminary events and `count=201`, page 2 contains Final. Assert only events whose `league_id===meta.leagueId` and `coppaStageKey()!=null` remain, and both offsets `0` and `200` are requested.

- [ ] **Step 5: Implement paginated Coppa fetch**

```js
export async function fetchCoppaEvents({findSeedEvent,bsd}){
  const meta=await discoverCompetitionMeta({competition:'coppa_italia',findSeedEvent,bsd});
  const events=[];
  for(let offset=0;offset<1000;offset+=200){
    const page=await bsd(`/events/?season_id=${meta.seasonId}&limit=200&offset=${offset}`);
    const rows=Array.isArray(page?.results)?page.results:Array.isArray(page)?page:[];
    events.push(...rows.filter(e=>Number(e?.league_id)===meta.leagueId));
    const count=Number(page?.count??events.length);
    if(!rows.length||offset+rows.length>=count||rows.length<200)break;
  }
  const normalized=events.map(e=>normalizeCoppaEvent(e)).filter(Boolean);
  if(!normalized.some(e=>e.stage_key==='r32'))throw new Error('coppa_r32_missing');
  return {meta,events:normalized};
}
```

Do not invent future participants. An event is emitted only when the provider exposes a real event ID; UI placeholders are created later from missing bracket slots.

- [ ] **Step 6: Run tests and commit**

```bash
node --test work/tournament-tables/backend/tests/coppa.test.mjs work/tournament-tables/backend/tests/domain.test.mjs work/tournament-tables/backend/tests/provider.test.mjs
git add work/tournament-tables/backend
git commit -m "feat: normalize complete Coppa bracket events"
```

---

### Task 4: Implement repository, cache service, and external Match Center upserts

**Files:**
- Create: `work/tournament-tables/backend/service.mjs`
- Create: `work/tournament-tables/backend/tests/service.test.mjs`

**Interfaces:**
- Consumes provider functions from Tasks 2–3.
- Repository interface:
  - `findSeedEvent(competition)`
  - `localTeams()`
  - `readCache(season,competition,viewType)`
  - `writeCache(row)`
  - `upsertExternalMatches(rows): Promise<Map<number,number>>` mapping provider event ID -> numeric `cp_external_matches.id`.
- Produces `createTournamentTablesService({repository,provider,now})` with methods `standings(competition)` and `bracket()`.

- [ ] **Step 1: Write failing stale-cache service tests**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { createTournamentTablesService } from '../service.mjs';

test('standings returns stale last-good cache when provider fails', async()=>{
  const cached={payload:{rows:[{position:1}]},fetched_at:'2026-09-09T00:00:00Z',expires_at:'2026-09-09T00:01:00Z'};
  const service=createTournamentTablesService({now:()=>Date.parse('2026-09-09T00:02:00Z'),repository:{readCache:async()=>cached,localTeams:async()=>[],writeCache:async()=>{},findSeedEvent:async()=>1},provider:{fetchUefaView:async()=>{throw new Error('BSD 503')}}});
  const result=await service.standings('ucl');
  assert.equal(result.stale,true);
  assert.deepEqual(result.rows,[{position:1}]);
});

test('empty provider standings never replace valid cache', async()=>{
  let writes=0;
  const service=createTournamentTablesService({repository:{readCache:async()=>({payload:{rows:Array.from({length:36},(_,i)=>({position:i+1}))},expires_at:'2000-01-01T00:00:00Z'}),localTeams:async()=>[],writeCache:async()=>{writes++}},provider:{fetchUefaView:async()=>({meta:{},rows:[]})}});
  const result=await service.standings('ucl');
  assert.equal(result.stale,true);
  assert.equal(writes,0);
});
```

- [ ] **Step 2: Run RED**

```bash
node --test work/tournament-tables/backend/tests/service.test.mjs
```

Expected: FAIL because service is missing.

- [ ] **Step 3: Implement cache policy**

Use season label `2026/27` derived from current UTC month/year. Implement TTL constants:

```js
const TTL={standings:{live:30_000,idle:300_000},bracket:{live:15_000,idle:300_000}};
```

A cached row is fresh when `Date.parse(expires_at)>now()`. Provider payload is valid only when UEFA rows are exactly 36 unique positions or Coppa has at least one `r32` event.

- [ ] **Step 4: Write external-match upsert contract test**

Create fake Coppa events with provider IDs `7001` and `7002`; fake repository returns `Map([[7001,41],[7002,42]])`; assert service output embeds `external_match_id:41/42` into the corresponding bracket event and preserves stage keys.

- [ ] **Step 5: Implement bracket service flow**

The flow must be:

```js
const raw=await provider.fetchCoppaEvents({findSeedEvent:repository.findSeedEvent,bsd:provider.bsd});
const localTeams=await repository.localTeams();
const normalized=raw.events.map(e=>provider.localizeCoppaEvent(e,localTeams));
const idMap=await repository.upsertExternalMatches(normalized);
const withIds=normalized.map(e=>({...e,external_match_id:idMap.get(e.provider_event_id)??null}));
```

Group output rounds in fixed order `r32,r16,qf,sf,final`. Stage labels are `1/16`, `1/8`, `1/4`, `1/2`, `Финал`. Never fabricate `external_match_id`.

- [ ] **Step 6: Run service tests and commit**

```bash
node --test work/tournament-tables/backend/tests/*.test.mjs
git add work/tournament-tables/backend
git commit -m "feat: add tournament table cache service"
```

---

### Task 5: Build and deploy `ciao-tournament-tables-v1`

**Files:**
- Create: `work/tournament-tables/backend/index.ts`
- Create: `work/tournament-tables/backend/auth.mjs`
- Create: `work/tournament-tables/backend/tests/http-contract.test.mjs`

**Interfaces:**
- HTTP POST `{action:'standings',competition:'ucl|uel|uecl'}` -> standings response.
- HTTP POST `{action:'bracket',competition:'coppa_italia'}` -> bracket response.
- GET -> service metadata only.

- [ ] **Step 1: Write HTTP contract test against exported request handler**

Structure `index.ts` so request dispatch is a pure exported `handleRequest(req,deps)` plus final `Deno.serve(req=>handleRequest(req,prodDeps))`.

Test invalid calls:

```js
assert.equal((await handleRequest(jsonReq({action:'standings',competition:'coppa_italia'}),deps)).status,400);
assert.equal((await handleRequest(jsonReq({action:'bracket',competition:'ucl'}),deps)).status,400);
```

Test auth failure returns `401/403` and no provider method is called.

- [ ] **Step 2: Run RED**

```bash
node --test work/tournament-tables/backend/tests/http-contract.test.mjs
```

Expected: FAIL because `index.ts` is missing.

- [ ] **Step 3: Implement production repository and auth**

Copy the proven Telegram validation/channel membership behavior from `ciao-club-profile-fast` / `ciao-match-center-fast-v3` into focused `auth.mjs`.

Production repository queries:

```js
findSeedEvent: async competition => {
  const q=await db.from('cp_external_matches').select('provider_event_id').eq('competition',competition).order('kickoff_at',{ascending:true}).limit(1).maybeSingle();
  if(q.error)throw q.error;return q.data?.provider_event_id??null;
},
localTeams: async()=>{
  const q=await db.from('cp_teams').select('id,name,short_name,custom_emoji_id,bsd_team_id').not('bsd_team_id','is',null);
  if(q.error)throw q.error;return q.data??[];
}
```

`upsertExternalMatches` writes existing `cp_external_matches` columns using `competition='coppa_italia'`, `provider='bsd'`, canonical stage key/order, kickoff/status/team/score fields, with `onConflict:'competition,provider_event_id'`, then selects `id,provider_event_id`.

- [ ] **Step 4: Implement request dispatch and response shape**

GET response:

```json
{"ok":true,"service":"ciao-tournament-tables-v1","version":1,"competitions":["ucl","uel","uecl","coppa_italia"]}
```

For authenticated POST, return top-level `{ok:true,...serviceResult}`. Typed errors:

- `invalid_competition` -> 400
- `competition_seed_missing` -> 503
- `provider_unavailable` -> 503 when no cache exists
- `subscription_required` -> 403
- invalid Telegram auth -> 401

- [ ] **Step 5: Run full backend tests**

```bash
node --test work/tournament-tables/backend/tests/*.test.mjs
```

Expected: all PASS.

- [ ] **Step 6: Deploy Edge Function**

Deploy `index.ts`, `auth.mjs`, `domain.mjs`, `provider.mjs`, `service.mjs` as `ciao-tournament-tables-v1` with `verify_jwt=false` because custom Telegram auth is enforced in `handleRequest`.

- [ ] **Step 7: Smoke-test real provider coverage before frontend work**

Using an authenticated Mini App request, verify:

```text
ucl: rows.length = 36, unique positions = 36
uel: rows.length = 36, unique positions = 36
uecl: rows.length = 36, unique positions = 36
coppa_italia: rounds include r32 and every actual returned event has external_match_id > 0
```

Also query `cp_external_matches` and confirm Coppa provider IDs remain unique under `(competition, provider_event_id)`.

- [ ] **Step 8: Verify stale-cache behavior with a controlled provider failure test**

Do not break production credentials. Unit-test the failure path and then verify a second API request reads the newly populated cache row. Confirm cache row count is exactly one per `(season,competition,view_type)`.

- [ ] **Step 9: Commit backend implementation branch**

```bash
git add work/tournament-tables/backend
git commit -m "feat: deploy tournament tables API"
```

Do not merge these backend source files or migration files into production `main`; keep them on the feature/implementation branch as the auditable source used for deployment.
