import test from 'node:test';
import assert from 'node:assert/strict';
import { createApiClient } from '../api.js';

test('sends Telegram init data on every request', async () => {
  let seen;
  const api = createApiClient({ baseUrl:'https://api.test', initData:'signed', fetchImpl: async (url, init) => {
    seen = { url:String(url), init };
    return new Response(JSON.stringify({ ok:true, data:{ value:1 } }), { status:200, headers:{'content-type':'application/json'} });
  }});
  const result = await api.get('/api/qpf/dashboard');
  assert.equal(result.value, 1);
  assert.equal(seen.init.headers['x-telegram-init-data'], 'signed');
});

test('throws backend error code for rejected request', async () => {
  const api = createApiClient({ initData:'bad', fetchImpl: async () => new Response(JSON.stringify({ ok:false, error:'admin_access_denied' }), { status:403, headers:{'content-type':'application/json'} }) });
  await assert.rejects(() => api.get('/api/qpf/employees'), /admin_access_denied/);
});

test('posts JSON payload', async () => {
  let body;
  const api = createApiClient({ initData:'signed', fetchImpl: async (_url, init) => {
    body = JSON.parse(init.body);
    return new Response(JSON.stringify({ ok:true, data:{ id:'e1' } }), { status:201, headers:{'content-type':'application/json'} });
  }});
  const result = await api.post('/api/qpf/employees', { fullName:'Анна' });
  assert.deepEqual(body, { fullName:'Анна' });
  assert.equal(result.id, 'e1');
});
