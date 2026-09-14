export function createApiClient({ baseUrl = '', initData = '', fetchImpl = fetch }) {
  async function request(path, options = {}) {
    const headers = {
      'x-telegram-init-data': initData,
      ...(options.body ? { 'content-type': 'application/json' } : {}),
      ...(options.headers || {}),
    };
    const response = await fetchImpl(`${baseUrl}${path}`, {
      ...options,
      headers,
      body: options.body && typeof options.body !== 'string' ? JSON.stringify(options.body) : options.body,
    });
    let payload = null;
    try { payload = await response.json(); } catch {}
    if (!response.ok || payload?.ok === false) {
      throw new Error(payload?.error || `http_${response.status}`);
    }
    return payload?.data ?? payload;
  }
  return {
    get: (path) => request(path),
    post: (path, body) => request(path, { method:'POST', body }),
  };
}
