import test from 'node:test';
import assert from 'node:assert/strict';
import { createWorker } from '../src/worker.js';

const env = { TELEGRAM_BOT_TOKEN: 'token' };
const admin = { id: 'a1', telegram_id: 446763142, display_name: 'Админ 1' };

function deps(overrides = {}) {
  return {
    validateInitData: async () => ({ user: { id: 446763142 } }),
    findAdmin: async () => admin,
    getDashboard: async () => ({ profit: 10 }),
    listEmployees: async () => [{ id: 'e1' }],
    listEvents: async () => [{ id: 'v1' }],
    getEventDetail: async (id) => id === 'v1' ? { event: { id } } : null,
    listReferences: async () => ({ units: [] }),
    createReference: async (body) => ({ id: 'ref-1', ...body }),
    archiveReference: async (body) => ({ id: body.id, is_active: false }),
    createEmployee: async (body) => ({ id: 'e2', ...body }),
    createEvent: async (body) => body,
    createEventJob: async (body) => body,
    createIncome: async (body) => body,
    createExpense: async (body) => body,
    createAccrual: async (body) => body,
    createPayment: async (body) => body,
    annulEntity: async (body) => body,
    ...overrides,
  };
}

function req(path, options = {}) {
  return new Request(`https://finance.test${path}`, {
    ...options,
    headers: {
      'x-telegram-init-data': 'signed-data',
      ...(options.body ? { 'content-type': 'application/json' } : {}),
      ...(options.headers || {}),
    },
  });
}

test('rejects protected API without Telegram init data', async () => {
  const worker = createWorker(deps());
  const response = await worker.fetch(new Request('https://finance.test/api/qpf/employees'), env);
  assert.equal(response.status, 401);
  assert.equal((await response.json()).error, 'telegram_init_data_required');
});

test('returns reference dictionaries for an authorized admin', async () => {
  const worker = createWorker(deps({ listReferences: async () => ({ units: [{ code: 'moscow' }] }) }));
  const response = await worker.fetch(req('/api/qpf/references'), env);
  assert.equal(response.status, 200);
  assert.deepEqual((await response.json()).data.units, [{ code: 'moscow' }]);
});

test('creates an editable reference through the protected API', async () => {
  let received;
  const worker = createWorker(deps({ createReference: async (body) => { received = body; return { id: 'c1', name: body.name }; } }));
  const body = { kind: 'regionCity', name: 'Казань' };
  const response = await worker.fetch(req('/api/qpf/references', { method: 'POST', body: JSON.stringify(body) }), env);
  assert.equal(response.status, 201);
  assert.deepEqual(received, body);
});

test('archives a reference instead of deleting it', async () => {
  let received;
  const worker = createWorker(deps({ archiveReference: async (body) => { received = body; return { id: body.id, is_active: false }; } }));
  const body = { kind: 'duty', id: 'd1' };
  const response = await worker.fetch(req('/api/qpf/references/archive', { method: 'POST', body: JSON.stringify(body) }), env);
  assert.equal(response.status, 200);
  assert.deepEqual(received, body);
  assert.equal((await response.json()).data.is_active, false);
});

test('returns one event detail by id', async () => {
  const worker = createWorker(deps());
  const response = await worker.fetch(req('/api/qpf/events/v1'), env);
  assert.equal(response.status, 200);
  assert.equal((await response.json()).data.event.id, 'v1');
});

test('returns 404 for unknown event detail', async () => {
  const worker = createWorker(deps());
  const response = await worker.fetch(req('/api/qpf/events/missing'), env);
  assert.equal(response.status, 404);
  assert.equal((await response.json()).error, 'event_not_found');
});

test('passes event job duties to the create handler', async () => {
  let received;
  const worker = createWorker(deps({ createEventJob: async (body) => { received = body; return { id: 'j1' }; } }));
  const body = { eventId: 'v1', employeeId: 'e1', roleId: 'r1', dutyIds: ['d1','d2'] };
  const response = await worker.fetch(req('/api/qpf/event-jobs', { method: 'POST', body: JSON.stringify(body) }), env);
  assert.equal(response.status, 201);
  assert.deepEqual(received.dutyIds, ['d1','d2']);
});
