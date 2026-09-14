import test from 'node:test';
import assert from 'node:assert/strict';
import { createEventJobWithDuties } from '../src/eventJobs.js';

test('creates event job through RPC with duties and admin id', async () => {
  let seen;
  const fetchImpl = async (url, init) => {
    seen = { url: String(url), init, body: JSON.parse(init.body) };
    return new Response(JSON.stringify({ id: 'job-1', total_amount: 4500 }), { status: 200, headers: { 'content-type': 'application/json' } });
  };
  const result = await createEventJobWithDuties({
    eventId: 'event-1', employeeId: 'employee-1', roleId: 'role-1', rateType: 'hourly',
    rateAmount: 1000, quantity: 4.5, dutyIds: ['duty-1','duty-2'],
  }, {
    SUPABASE_URL: 'https://project.test', SUPABASE_SERVICE_ROLE_KEY: 'service-key',
  }, { id: 'admin-1' }, fetchImpl);

  assert.match(seen.url, /rpc\/qpf_create_event_job$/);
  assert.equal(seen.body.p_quantity, 4.5);
  assert.deepEqual(seen.body.p_duty_ids, ['duty-1','duty-2']);
  assert.equal(seen.body.p_created_by, 'admin-1');
  assert.equal(result.id, 'job-1');
});
