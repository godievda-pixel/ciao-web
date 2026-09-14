function serviceHeaders(env) {
  return {
    apikey: env.SUPABASE_SERVICE_ROLE_KEY,
    authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
    accept: 'application/json',
  };
}

async function get(table, params, env, fetchImpl = fetch) {
  const url = new URL(`/rest/v1/${table}`, env.SUPABASE_URL);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, value);
  }
  const response = await fetchImpl(url, { headers: serviceHeaders(env) });
  if (!response.ok) throw new Error(`supabase_${table}_failed:${response.status}`);
  return response.json();
}

export async function listReferences(env, fetchImpl = fetch) {
  const [units, eventTypes, roles, duties, incomeSources, expenseCategories, paymentMethods, regionCities] = await Promise.all([
    get('qpf_units', { select: 'code,name,sort_order', is_active: 'eq.true', order: 'sort_order.asc' }, env, fetchImpl),
    get('qpf_event_types', { select: 'id,name', is_active: 'eq.true', order: 'name.asc' }, env, fetchImpl),
    get('qpf_roles', { select: 'id,name,role_scope,default_rate_type,default_rate', is_active: 'eq.true', order: 'name.asc' }, env, fetchImpl),
    get('qpf_duties', { select: 'id,name', is_active: 'eq.true', order: 'name.asc' }, env, fetchImpl),
    get('qpf_income_sources', { select: 'id,name', is_active: 'eq.true', order: 'name.asc' }, env, fetchImpl),
    get('qpf_expense_categories', { select: 'id,name', is_active: 'eq.true', order: 'name.asc' }, env, fetchImpl),
    get('qpf_payment_methods', { select: 'id,name,method_code,is_employee_personal', is_active: 'eq.true', order: 'name.asc' }, env, fetchImpl),
    get('qpf_region_cities', { select: 'id,name', is_active: 'eq.true', order: 'name.asc' }, env, fetchImpl),
  ]);

  return {
    units: units.map((x) => ({ code: x.code, name: x.name })),
    eventTypes: eventTypes.map((x) => ({ id: x.id, name: x.name })),
    roles: roles.map((x) => ({ id: x.id, name: x.name, scope: x.role_scope, defaultRateType: x.default_rate_type, defaultRate: x.default_rate == null ? null : Number(x.default_rate) })),
    duties: duties.map((x) => ({ id: x.id, name: x.name })),
    incomeSources: incomeSources.map((x) => ({ id: x.id, name: x.name })),
    expenseCategories: expenseCategories.map((x) => ({ id: x.id, name: x.name })),
    paymentMethods: paymentMethods.map((x) => ({ id: x.id, name: x.name, code: x.method_code, isEmployeePersonal: x.is_employee_personal })),
    regionCities: regionCities.map((x) => ({ id: x.id, name: x.name })),
  };
}
