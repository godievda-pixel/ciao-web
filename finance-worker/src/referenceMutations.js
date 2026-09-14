const REFERENCE_TABLES = {
  regionCity: 'qpf_region_cities',
  duty: 'qpf_duties',
  incomeSource: 'qpf_income_sources',
  expenseCategory: 'qpf_expense_categories',
  eventType: 'qpf_event_types',
  role: 'qpf_roles',
  paymentMethod: 'qpf_payment_methods',
};

function tableFor(kind) {
  const table = REFERENCE_TABLES[kind];
  if (!table) throw new Error('reference_kind_not_allowed');
  return table;
}

function headers(env, admin) {
  return {
    apikey: env.SUPABASE_SERVICE_ROLE_KEY,
    authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
    accept: 'application/json',
    'content-type': 'application/json',
    prefer: 'return=representation',
    'x-qpf-admin-id': admin.id,
    'x-qpf-source': 'app',
  };
}

function createBody(payload) {
  const name = String(payload.name ?? '').trim();
  if (!name) throw new Error('reference_name_required');

  if (payload.kind === 'role') {
    return {
      name,
      role_scope: payload.scope ?? 'event',
      default_rate_type: payload.defaultRateType || null,
      default_rate: payload.defaultRate === '' || payload.defaultRate == null ? null : Number(payload.defaultRate),
    };
  }

  if (payload.kind === 'paymentMethod') {
    return {
      name,
      method_code: payload.code || null,
      is_employee_personal: Boolean(payload.isEmployeePersonal),
    };
  }

  return { name };
}

export async function createReference(payload, env, admin, fetchImpl = fetch) {
  const table = tableFor(payload.kind);
  const url = new URL(`/rest/v1/${table}`, env.SUPABASE_URL);
  const response = await fetchImpl(url, {
    method: 'POST',
    headers: headers(env, admin),
    body: JSON.stringify(createBody(payload)),
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => '');
    throw new Error(`reference_create_failed:${response.status}:${detail}`);
  }
  const rows = await response.json();
  return rows[0] ?? null;
}

export async function archiveReference(payload, env, admin, fetchImpl = fetch) {
  const table = tableFor(payload.kind);
  if (!payload.id) throw new Error('reference_id_required');
  const url = new URL(`/rest/v1/${table}`, env.SUPABASE_URL);
  url.searchParams.set('id', `eq.${payload.id}`);
  const response = await fetchImpl(url, {
    method: 'PATCH',
    headers: headers(env, admin),
    body: JSON.stringify({ is_active: false }),
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => '');
    throw new Error(`reference_archive_failed:${response.status}:${detail}`);
  }
  const rows = await response.json();
  return rows[0] ?? null;
}
