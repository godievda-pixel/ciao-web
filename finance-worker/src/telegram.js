const encoder = new TextEncoder();

async function hmacSha256(key, message) {
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    typeof key === 'string' ? encoder.encode(key) : key,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  return new Uint8Array(await crypto.subtle.sign('HMAC', cryptoKey, encoder.encode(message)));
}

function toHex(bytes) {
  return [...bytes].map((b) => b.toString(16).padStart(2, '0')).join('');
}

export async function validateTelegramInitData(initData, botToken, options = {}) {
  const params = new URLSearchParams(initData);
  const suppliedHash = params.get('hash');
  const dataCheckString = [...params.entries()]
    .filter(([key]) => key !== 'hash')
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => `${key}=${value}`)
    .join('\n');

  const secretKey = await hmacSha256('WebAppData', botToken);
  const expectedHash = toHex(await hmacSha256(secretKey, dataCheckString));
  if (suppliedHash?.toLowerCase() !== expectedHash) {
    throw new Error('telegram_signature_invalid');
  }

  const authDate = Number(params.get('auth_date'));
  const nowSeconds = options.nowSeconds ?? Math.floor(Date.now() / 1000);
  const maxAgeSeconds = options.maxAgeSeconds ?? 900;
  if (!Number.isFinite(authDate) || nowSeconds - authDate > maxAgeSeconds) {
    throw new Error('telegram_auth_expired');
  }

  return {
    user: JSON.parse(params.get('user')),
    authDate,
  };
}
