function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

export function createWorker(deps = {}) {
  return {
    async fetch(request, env) {
      const url = new URL(request.url);
      if (request.method === 'GET' && url.pathname === '/api/qpf/health') {
        return json({ ok: true, service: 'qpf-finance-api' });
      }
      if (request.method === 'POST' && url.pathname === '/api/qpf/session') {
        const initData = request.headers.get('x-telegram-init-data');
        if (!initData) {
          return json({ ok: false, error: 'telegram_init_data_required' }, 401);
        }

        let session;
        try {
          session = await deps.validateInitData(initData, env.TELEGRAM_BOT_TOKEN);
        } catch {
          return json({ ok: false, error: 'telegram_auth_invalid' }, 401);
        }
        const admin = await deps.findAdmin(session.user.id, env);
        if (!admin) {
          return json({ ok: false, error: 'admin_access_denied' }, 403);
        }
        return json({
          ok: true,
          admin: {
            id: admin.id,
            telegramId: admin.telegram_id,
            displayName: admin.display_name,
          },
        });
      }
      return new Response('not found', { status: 404 });
    },
  };
}
