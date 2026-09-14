import test from 'node:test';
import assert from 'node:assert/strict';
import { createReference, archiveReference } from '../src/referenceMutations.js';

const env = { SUPABASE_URL:'https://project.test', SUPABASE_SERVICE_ROLE_KEY:'key' };
const admin = { id:'admin-1' };

test('creates a regional city only in the allowed table', async () => {
  let seen;
  const fetchImpl = async (url, init) => {
    seen = { url:String(url), init, body:JSON.parse(init.body) };
    return new Response(JSON.stringify([{ id:'c1', name:'Казань' }]), { status:201, headers:{'content-type':'application/json'} });
  };
  const result = await createReference({ kind:'regionCity', name:'Казань' }, env, admin, fetchImpl);
  assert.match(seen.url, /qpf_region_cities$/);
  assert.equal(seen.body.name, 'Казань');
  assert.equal(result.id, 'c1');
});

test('rejects an unknown reference kind before making a request', async () => {
  await assert.rejects(() => createReference({ kind:'anything', name:'X' }, env, admin, async () => { throw new Error('must not fetch'); }), /reference_kind_not_allowed/);
});

test('archives a reference instead of deleting it', async () => {
  let seen;
  const fetchImpl = async (url, init) => {
    seen = { url:String(url), init, body:JSON.parse(init.body) };
    return new Response(JSON.stringify([{ id:'d1', is_active:false }]), { status:200, headers:{'content-type':'application/json'} });
  };
  await archiveReference({ kind:'duty', id:'d1' }, env, admin, fetchImpl);
  assert.equal(seen.init.method, 'PATCH');
  assert.equal(seen.body.is_active, false);
  assert.match(seen.url, /id=eq\.d1/);
});
