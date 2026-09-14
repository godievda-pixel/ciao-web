import test from 'node:test';
import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import { validateTelegramInitData } from '../src/telegram.js';

function signInitData({ botToken, authDate, user, queryId = 'AAE-test' }) {
  const params = new URLSearchParams();
  params.set('auth_date', String(authDate));
  params.set('query_id', queryId);
  params.set('user', JSON.stringify(user));
  const dataCheckString = [...params.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => `${key}=${value}`)
    .join('\n');
  const secretKey = createHmac('sha256', 'WebAppData').update(botToken).digest();
  const hash = createHmac('sha256', secretKey).update(dataCheckString).digest('hex');
  params.set('hash', hash);
  return params.toString();
}

test('accepts valid Telegram initData and returns the Telegram user', async () => {
  const now = 1789400000;
  const initData = signInitData({
    botToken: '123456:test-token',
    authDate: now - 10,
    user: { id: 446763142, first_name: 'Daniil', username: 'testadmin' },
  });
  const result = await validateTelegramInitData(initData, '123456:test-token', {
    nowSeconds: now,
    maxAgeSeconds: 900,
  });
  assert.equal(result.user.id, 446763142);
  assert.equal(result.user.username, 'testadmin');
});

test('rejects tampered Telegram initData', async () => {
  const now = 1789400000;
  const initData = signInitData({
    botToken: '123456:test-token',
    authDate: now - 10,
    user: { id: 446763142, first_name: 'Daniil' },
  });
  const params = new URLSearchParams(initData);
  params.set('user', JSON.stringify({ id: 999, first_name: 'Intruder' }));
  await assert.rejects(
    () => validateTelegramInitData(params.toString(), '123456:test-token', { nowSeconds: now, maxAgeSeconds: 900 }),
    /telegram_signature_invalid/,
  );
});

test('rejects expired Telegram initData', async () => {
  const now = 1789400000;
  const initData = signInitData({
    botToken: '123456:test-token',
    authDate: now - 901,
    user: { id: 446763142, first_name: 'Daniil' },
  });
  await assert.rejects(
    () => validateTelegramInitData(initData, '123456:test-token', { nowSeconds: now, maxAgeSeconds: 900 }),
    /telegram_auth_expired/,
  );
});
