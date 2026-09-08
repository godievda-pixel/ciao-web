// @ts-nocheck
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.112.4";

const SB_URL=Deno.env.get("SUPABASE_URL")??"",V5=`${SB_URL}/functions/v1/ciao-core-api-fast-v5`;
const ALLOWED_ORIGINS=new Set(["https://godievda-pixel.github.io","https://ciao-web-app.orderly-bulb.workers.dev","https://ciao-web-app.ciao-web.workers.dev"]);
const RATING_SEASON='2026/27';
const RATING_SEASON_START='2026-07-01T00:00:00Z';
const RATING_SEASON_END='2027-07-01T00:00:00Z';
const RATING_COMPETITIONS=new Set(['all','serie_a','ucl','uel','uecl','coppa_italia']);
const RATING_CACHE_TTL=30000;

function serviceKey(){const s=Deno.env.get("SUPABASE_SECRET_KEYS");if(s){try{const j=JSON.parse(s);if(typeof j?.default==="string")return j.default;const x=Object.values(j??{}).find(v=>typeof v==="string");if(x)return String(x)}catch{}}return Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")??""}
const db=createClient(SB_URL,serviceKey(),{auth:{persistSession:false}});
function cors(req){const origin=req.headers.get("origin")??"";return{"access-control-allow-origin":ALLOWED_ORIGINS.has(origin)?origin:"https://godievda-pixel.github.io","access-control-allow-methods":"GET,POST,OPTIONS","access-control-allow-headers":"content-type,x-telegram-init-data","access-control-max-age":"86400","vary":"Origin"}}
const out=(req,x,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors(req),"content-type":"application/json; charset=utf-8","cache-control":"no-store"}});
async function proxy(req,b){const r=await fetch(V5,{method:"POST",headers:{"content-type":"application/json","x-telegram-init-data":req.headers.get("x-telegram-init-data")??""},body:JSON.stringify(b)}),j=await r.json().catch(()=>({}));return{r,j}}
async function authState(req){const x=await proxy(req,{action:'state'});return x.r.ok&&x.j?.ok?{ok:true,state:x.j}:{ok:false,response:out(req,x.j,x.r.status)}}
function telegramId(req){try{const p=new URLSearchParams(req.headers.get("x-telegram-init-data")??""),u=JSON.parse(p.get("user")??"null");return Number(u?.id)||0}catch{return 0}}
function team(t){return t?{id:Number(t.id),name:String(t.name??""),short_name:t.short_name??null,custom_emoji_id:t.custom_emoji_id??null}:null}
function normalize(m){return{match_id:Number(m.id),id:Number(m.id),kickoff_at:m.kickoff_at??null,nominal_date:m?.round?.nominal_date??null,round_number:m?.round?.number??null,home:team(m.home),away:team(m.away),home_score:m.home_score??null,away_score:m.away_score??null,is_finished:!!m.is_finished,live_status:m.live_status??null,live_elapsed:m.live_elapsed??null,live_phase:m.live_phase??null}}
function scheduleTs(m){const exact=Date.parse(String(m?.kickoff_at||''));if(Number.isFinite(exact))return exact;const nominal=Date.parse(String(m?.nominal_date||''));return Number.isFinite(nominal)?nominal+12*3600000:Number.POSITIVE_INFINITY}
function resultForTeam(m,teamId){const home=Number(m?.home?.id)===Number(teamId),gf=Number(home?m?.home_score:m?.away_score),ga=Number(home?m?.away_score:m?.home_score);return gf>ga?'W':gf<ga?'L':'D'}
function withoutRoundBonus(payload){if(!payload||typeof payload!=="object")return payload;if(payload.rules&&typeof payload.rules==="object")payload.rules={...payload.rules,bonus_multiplier:1,bonus_per_round:0,bonus_enabled:false};if(payload.round_summary&&typeof payload.round_summary==="object")payload.round_summary={...payload.round_summary,bonus_selected:false,bonus_locked:true};payload.round_bonus={match_id:null,selected_at:null,updated_at:null,locked:true,can_choose:false,can_move:false,available_match_ids:[],disabled:true,removed:true};return payload}
async function eagerFavorite(req){const tid=telegramId(req);if(!tid)return null;const uq=await db.from("cp_users").select("favorite_team_id").eq("telegram_id",tid).maybeSingle();if(uq.error||!uq.data?.favorite_team_id)return null;const id=Number(uq.data.favorite_team_id);const [tq,mq]=await Promise.all([db.from("cp_teams").select("id,name,short_name,custom_emoji_id").eq("id",id).maybeSingle(),db.from("cp_matches").select("id,kickoff_at,home_score,away_score,is_finished,live_status,live_elapsed,live_phase,round:cp_rounds!cp_matches_round_fk(number,nominal_date),home:cp_teams!cp_matches_home_team_fk(id,name,short_name,custom_emoji_id),away:cp_teams!cp_matches_away_team_fk(id,name,short_name,custom_emoji_id)").or(`home_team_id.eq.${id},away_team_id.eq.${id}`).order("round_id",{ascending:true})]);if(tq.error||mq.error||!tq.data)return null;const all=(mq.data??[]).map(normalize),finished=all.filter(x=>x.is_finished).sort((a,b)=>scheduleTs(b)-scheduleTs(a)),upcoming=all.filter(x=>!x.is_finished).sort((a,b)=>scheduleTs(a)-scheduleTs(b));const form=finished.slice(0,5).map(m=>({result:resultForTeam(m,id),match_id:m.id,home_team:m.home?.name??null,away_team:m.away?.name??null,home_score:m.home_score,away_score:m.away_score,kickoff_at:m.kickoff_at,nominal_date:m.nominal_date??null}));return{ok:true,team:team(tq.data),coverage:{overview:true},overview:{form,last_match:finished[0]??null,next_match:upcoming[0]??null}}}

function inRatingSeason(value){const t=Date.parse(String(value||'')),a=Date.parse(RATING_SEASON_START),b=Date.parse(RATING_SEASON_END);return Number.isFinite(t)&&t>=a&&t<b}
function serieDate(match,round){if(match?.kickoff_at)return String(match.kickoff_at);return round?.nominal_date?`${round.nominal_date}T12:00:00Z`:null}
function cmpResultTime(a,b){return Date.parse(String(b.settled_at||''))-Date.parse(String(a.settled_at||''))||String(b.source).localeCompare(String(a.source))||Number(b.source_id)-Number(a.source_id)}
const ratingCache=new Map();

async function loadRatingBase(){
  const [uq,tq,pq,mq,rq,epq,emq,sq]=await Promise.all([
    db.from('cp_users').select('id,display_name,favorite_team_id').eq('is_active',true),
    db.from('cp_teams').select('id,name,short_name,custom_emoji_id'),
    db.from('cp_predictions').select('id,user_id,match_id,points,base_points').not('points','is',null),
    db.from('cp_matches').select('id,round_id,kickoff_at,home_score,away_score,is_finished'),
    db.from('cp_rounds').select('id,number,nominal_date'),
    db.from('cp_external_predictions').select('id,user_id,external_match_id,points,base_points').not('points','is',null),
    db.from('cp_external_matches').select('id,competition,stage_key,stage_order,round_number,kickoff_at,status,home_score,away_score,finalized_at'),
    db.from('cp_scoring_rules').select('exact_score').eq('id',1).maybeSingle()
  ]);
  for(const q of [uq,tq,pq,mq,rq,epq,emq,sq])if(q.error)throw q.error;
  const users=uq.data??[],teams=new Map((tq.data??[]).map(t=>[Number(t.id),t]));
  const rounds=new Map((rq.data??[]).map(r=>[Number(r.id),r])),matches=new Map((mq.data??[]).map(m=>[Number(m.id),m]));
  const externalMatches=new Map((emq.data??[]).map(m=>[Number(m.id),m]));
  const results=[];
  for(const p of pq.data??[]){const m=matches.get(Number(p.match_id)),r=m?rounds.get(Number(m.round_id)):null,date=serieDate(m,r);if(!m||!date||!inRatingSeason(date))continue;results.push({source:'serie_a',competition:'serie_a',user_id:Number(p.user_id),source_id:Number(p.id),match_id:Number(p.match_id),settled_at:date,block_key:`serie_a:round:${Number(r?.number)||0}`,points:Number(p.points??0),base_points:Number(p.base_points??0)})}
  for(const p of epq.data??[]){const m=externalMatches.get(Number(p.external_match_id)),competition=String(m?.competition||'');if(!m||!RATING_COMPETITIONS.has(competition)||competition==='all'||competition==='serie_a'||!inRatingSeason(m.kickoff_at))continue;const block=String(m.stage_key||m.stage_order||m.round_number||'unknown');results.push({source:'external',competition,user_id:Number(p.user_id),source_id:Number(p.id),match_id:Number(p.external_match_id),settled_at:String(m.finalized_at||m.kickoff_at),block_key:`${competition}:stage:${block}`,points:Number(p.points??0),base_points:Number(p.base_points??0)})}
  return{users,teams,results,exactScore:Number(sq.data?.exact_score??5)};
}

function buildRatingRows(users,teams,results,exactScore){
  const by=new Map();for(const r of results){const a=by.get(Number(r.user_id))??[];a.push(r);by.set(Number(r.user_id),a)}
  const rows=users.map(u=>{const ps=(by.get(Number(u.id))??[]).slice().sort(cmpResultTime);let streak=0;for(const p of ps){if(Number(p.points)>0)streak++;else break}const successful=ps.filter(p=>Number(p.points)>0).length,calculated=ps.length,ft=teams.get(Number(u.favorite_team_id));return{id:Number(u.id),display_name:String(u.display_name??''),favorite_team:ft?team(ft):null,points:ps.reduce((s,p)=>s+Number(p.points||0),0),exact:ps.filter(p=>Number(p.base_points)===exactScore).length,successful,calculated,success_rate:calculated?Math.round(successful*100/calculated):0,streak,trend:0}});
  rows.sort((a,b)=>b.points-a.points||b.exact-a.exact||b.successful-a.successful||a.display_name.localeCompare(b.display_name,'ru'));
  rows.forEach((r,i)=>r.rank=i+1);return rows;
}

async function ratingStandings(competition='all'){
  competition=RATING_COMPETITIONS.has(String(competition))?String(competition):'all';
  const ck=`${RATING_SEASON}:${competition}`,cached=ratingCache.get(ck);if(cached&&cached.expires>Date.now())return cached.value;
  const base=await loadRatingBase(),selected=base.results.filter(r=>competition==='all'||r.competition===competition),rows=buildRatingRows(base.users,base.teams,selected,base.exactScore);
  if(selected.length){const blockTimes=new Map();for(const r of selected){const t=Date.parse(String(r.settled_at||''));if(!Number.isFinite(t))continue;blockTimes.set(r.block_key,Math.max(blockTimes.get(r.block_key)||0,t))}const latest=[...blockTimes.entries()].sort((a,b)=>b[1]-a[1])[0]?.[0];if(latest){const previousResults=selected.filter(r=>r.block_key!==latest);if(previousResults.length){const previous=buildRatingRows(base.users,base.teams,previousResults,base.exactScore),pm=new Map(previous.map(r=>[r.id,r.rank]));for(const r of rows)r.trend=Number(pm.get(r.id)??r.rank)-r.rank}}}
  const value={competition,rows,updated_at:new Date().toISOString(),season:RATING_SEASON};ratingCache.set(ck,{value,expires:Date.now()+RATING_CACHE_TTL});return value;
}

async function standingsAction(req,b){const a=await authState(req);if(!a.ok)return a.response;const competition=RATING_COMPETITIONS.has(String(b.competition))?String(b.competition):'all',x=await ratingStandings(competition);return out(req,{ok:true,competition:x.competition,standings:x.rows,standings_meta:{competition:x.competition,season:RATING_SEASON,updated_at:x.updated_at}})}

Deno.serve(async req=>{try{
  if(req.method==="OPTIONS")return new Response("ok",{headers:cors(req)});
  if(req.method==="GET")return out(req,{ok:true,service:"Ciao Core API Fast v6",version:6,eager_favorite:true,nominal_date_fallback:true,round_bonus:false,rating_competitions:[...RATING_COMPETITIONS],rating_season:RATING_SEASON,cors_origins:[...ALLOWED_ORIGINS]});
  if(req.method!=="POST")return new Response("Method Not Allowed",{status:405,headers:cors(req)});
  const b=await req.json().catch(()=>({})),action=String(b.action??"state");
  if(action==="set_round_bonus")return out(req,{ok:false,error:"Бонус x2 удалён из правил",code:"bonus_removed"},410);
  if(action==="standings_scope")return await standingsAction(req,b);
  if(action!=="state"){const x=await proxy(req,b);if(action==="prediction_rules"&&x.j?.rules)x.j.rules={...x.j.rules,bonus_multiplier:1,bonus_per_round:0,bonus_enabled:false};return out(req,x.j,x.r.status)}
  const baseP=proxy(req,b),favP=eagerFavorite(req).catch(()=>null),[base,favorite]=await Promise.all([baseP,favP]);if(!base.r.ok||!base.j?.ok)return out(req,base.j,base.r.status);withoutRoundBonus(base.j);if(favorite)base.j.favorite_club_profile=favorite;return out(req,base.j,base.r.status)
}catch(e){console.error("core_v6_error",e);return out(req,{ok:false,error:e instanceof Error?e.message:String(e)},500)}});
