export async function findActiveAdminByTelegramId(telegramId, env, fetchImpl = fetch) {
  const url = new URL('/rest/v1/qpf_admins', env.SUPABASE_URL);
  url.searchParams.set('telegram_id', `eq.${telegramId}`);
  url.searchParams.set('is_active', 'eq.true');
  url.searchParams.set('select', 'id,telegram_id,display_name,is_active');
  url.searchParams.set('limit', '1');

  const response = await fetchImpl(url, {
    headers: {
      apikey: env.SUPABASE_SERVICE_ROLE_KEY,
      authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
      accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`supabase_admin_lookup_failed:${response.status}`);
  }

  const rows = await response.json();
  return rows[0] ?? null;
}
