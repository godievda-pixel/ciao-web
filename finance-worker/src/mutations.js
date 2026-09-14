function serviceHeaders(env) {
  return {
    apikey: env.SUPABASE_SERVICE_ROLE_KEY,
    authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
    accept: 'application/json',
  };
}

function auditHeaders(env, admin, source = 'app') {
  return {
    ...serviceHeaders(env),
    'content-type': 'application/json',
    prefer: 'return=representation',
    'x-qpf-admin-id': admin.id,
    'x-qpf-source': source,
  };
}

async function supabaseWrite(table, body, env, admin, fetchImpl = fetch, options = {}) {
  const url = new URL(`/rest/v1/${table}`, env.SUPABASE_URL);
  for (const [key, value] of Object.entries(options.filters ?? {})) {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, value);
  }
  const response = await fetchImpl(url, {
    method: options.method ?? 'POST',
    headers: auditHeaders(env, admin, options.source ?? 'app'),
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => '');
    throw new Error(`supabase_${table}_write_failed:${response.status}:${detail}`);
  }
  const rows = await response.json();
  return rows[0] ?? null;
}

export function createEmployee(payload, env, admin, fetchImpl = fetch) {
  return supabaseWrite('qpf_employees', {
    full_name: payload.fullName,
    employee_type: payload.employeeType,
    organization_role_id: payload.organizationRoleId,
    phone: payload.phone,
    telegram_username: payload.telegramUsername,
    notes: payload.notes,
  }, env, admin, fetchImpl);
}

export function createEvent(payload, env, admin, fetchImpl = fetch) {
  return supabaseWrite('qpf_events', {
    event_type_id: payload.eventTypeId,
    unit_code: payload.unitCode,
    region_city_id: payload.regionCityId,
    title: payload.title,
    event_date: payload.eventDate,
    start_time: payload.startTime,
    end_time: payload.endTime,
    venue: payload.venue,
    notes: payload.notes,
    created_by: admin.id,
  }, env, admin, fetchImpl);
}

export function createEventJob(payload, env, admin, fetchImpl = fetch) {
  return supabaseWrite('qpf_event_jobs', {
    event_id: payload.eventId,
    employee_id: payload.employeeId,
    role_id: payload.roleId,
    rate_type: payload.rateType,
    rate_amount: payload.rateAmount,
    quantity: payload.quantity ?? 1,
    started_at: payload.startedAt,
    ended_at: payload.endedAt,
    notes: payload.notes,
    created_by: admin.id,
  }, env, admin, fetchImpl);
}

export function createIncome(payload, env, admin, fetchImpl = fetch) {
  return supabaseWrite('qpf_incomes', {
    event_id: payload.eventId,
    unit_code: payload.unitCode,
    source_id: payload.sourceId,
    description: payload.description,
    gross_amount: payload.grossAmount,
    tax_enabled: payload.taxEnabled ?? false,
    tax_rate: payload.taxRate ?? 9,
    income_date: payload.incomeDate,
    payment_method_id: payload.paymentMethodId,
    created_by: admin.id,
  }, env, admin, fetchImpl);
}

export function createExpense(payload, env, admin, fetchImpl = fetch) {
  return supabaseWrite('qpf_expenses', {
    event_id: payload.eventId,
    unit_code: payload.unitCode,
    category_id: payload.categoryId,
    description: payload.description,
    expense_kind: payload.expenseKind ?? 'organization',
    amount: payload.amount,
    expense_date: payload.expenseDate,
    payment_method_id: payload.paymentMethodId,
    paid_by_employee_id: payload.paidByEmployeeId,
    reimbursement_status: payload.reimbursementStatus ?? 'not_applicable',
    created_by: admin.id,
  }, env, admin, fetchImpl);
}

export function createAccrual(payload, env, admin, fetchImpl = fetch) {
  return supabaseWrite('qpf_accruals', {
    employee_id: payload.employeeId,
    unit_code: payload.unitCode,
    accrual_type: payload.accrualType,
    description: payload.description,
    amount: payload.amount,
    accrued_on: payload.accruedOn,
    created_by: admin.id,
  }, env, admin, fetchImpl);
}

export function createPayment(payload, env, admin, fetchImpl = fetch) {
  return supabaseWrite('qpf_payments', {
    employee_id: payload.employeeId,
    amount: payload.amount,
    paid_on: payload.paidOn,
    payment_method_id: payload.paymentMethodId,
    description: payload.description,
    created_by: admin.id,
  }, env, admin, fetchImpl);
}

const ANNUL_TABLES = {
  income: 'qpf_incomes',
  expense: 'qpf_expenses',
  accrual: 'qpf_accruals',
  payment: 'qpf_payments',
  event_job: 'qpf_event_jobs',
};

export async function annulEntity(payload, env, admin, fetchImpl = fetch) {
  const table = ANNUL_TABLES[payload.entityType];
  if (!table) throw new Error('annul_entity_not_allowed');
  return await supabaseWrite(table, {
    status: 'annulled',
    annul_reason: payload.reason,
    annulled_by: admin.id,
  }, env, admin, fetchImpl, {
    method: 'PATCH',
    filters: { id: `eq.${payload.entityId}` },
  });
}
