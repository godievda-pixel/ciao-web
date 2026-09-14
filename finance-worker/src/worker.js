function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

async function authenticateAdmin(request, env, deps) {
  const initData = request.headers.get('x-telegram-init-data');
  if (!initData) {
    return { response: json({ ok: false, error: 'telegram_init_data_required' }, 401) };
  }

  let session;
  try {
    session = await deps.validateInitData(initData, env.TELEGRAM_BOT_TOKEN);
  } catch {
    return { response: json({ ok: false, error: 'telegram_auth_invalid' }, 401) };
  }

  const admin = await deps.findAdmin(session.user.id, env);
  if (!admin) {
    return { response: json({ ok: false, error: 'admin_access_denied' }, 403) };
  }

  return { admin, session };
}

export function createWorker(deps = {}) {
  return {
    async fetch(request, env) {
      const url = new URL(request.url);
      if (request.method === 'GET' && url.pathname === '/api/qpf/health') {
        return json({ ok: true, service: 'qpf-finance-api' });
      }

      if (request.method === 'POST' && url.pathname === '/api/qpf/session') {
        const auth = await authenticateAdmin(request, env, deps);
        if (auth.response) return auth.response;
        return json({
          ok: true,
          admin: {
            id: auth.admin.id,
            telegramId: auth.admin.telegram_id,
            displayName: auth.admin.display_name,
          },
        });
      }

      if (url.pathname.startsWith('/api/qpf/')) {
        const auth = await authenticateAdmin(request, env, deps);
        if (auth.response) return auth.response;

        if (request.method === 'GET' && url.pathname === '/api/qpf/dashboard') {
          const data = await deps.getDashboard({
            month: url.searchParams.get('month'),
            unit: url.searchParams.get('unit'),
          }, env, auth.admin);
          return json({ ok: true, data });
        }

        if (request.method === 'GET' && url.pathname === '/api/qpf/employees') {
          const data = await deps.listEmployees(env, auth.admin);
          return json({ ok: true, data });
        }

        if (request.method === 'GET' && url.pathname === '/api/qpf/events') {
          const data = await deps.listEvents({
            unit: url.searchParams.get('unit'),
            from: url.searchParams.get('from'),
            to: url.searchParams.get('to'),
          }, env, auth.admin);
          return json({ ok: true, data });
        }
      }

      return new Response('not found', { status: 404 });
    },
  };
}
