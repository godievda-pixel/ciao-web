function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

async function readJsonBody(request) {
  try {
    const value = await request.json();
    if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
    return value;
  } catch {
    return null;
  }
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

        if (request.method === 'GET' && url.pathname === '/api/qpf/references') {
          const data = await deps.listReferences(env, auth.admin);
          return json({ ok: true, data });
        }

        if (request.method === 'POST') {
          const body = await readJsonBody(request);
          if (!body) return json({ ok: false, error: 'invalid_json' }, 400);

          const createRoutes = {
            '/api/qpf/employees': deps.createEmployee,
            '/api/qpf/events': deps.createEvent,
            '/api/qpf/event-jobs': deps.createEventJob,
            '/api/qpf/incomes': deps.createIncome,
            '/api/qpf/expenses': deps.createExpense,
            '/api/qpf/accruals': deps.createAccrual,
            '/api/qpf/payments': deps.createPayment,
          };
          const creator = createRoutes[url.pathname];
          if (creator) {
            const data = await creator(body, env, auth.admin);
            return json({ ok: true, data }, 201);
          }

          if (url.pathname === '/api/qpf/annul') {
            if (typeof body.reason !== 'string' || !body.reason.trim()) {
              return json({ ok: false, error: 'annul_reason_required' }, 400);
            }
            const data = await deps.annulEntity({ ...body, reason: body.reason.trim() }, env, auth.admin);
            return json({ ok: true, data });
          }
        }

        return json({ ok: false, error: 'not_found' }, 404);
      }

      if (env.ASSETS) return env.ASSETS.fetch(request);
      return new Response('not found', { status: 404 });
    },
  };
}
