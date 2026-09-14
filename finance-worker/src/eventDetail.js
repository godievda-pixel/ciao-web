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

const number = (value) => Number.isFinite(Number(value)) ? Number(value) : 0;
const inFilter = (values) => values.length ? `in.(${values.join(',')})` : null;

export async function getEventDetail(eventId, env, fetchImpl = fetch) {
  const [events, financialRows] = await Promise.all([
    get('qpf_events', {
      id: `eq.${eventId}`,
      select: 'id,event_type_id,unit_code,region_city_id,title,event_date,start_time,end_time,venue,status,notes',
      limit: '1',
    }, env, fetchImpl),
    get('qpf_event_financials', {
      event_id: `eq.${eventId}`,
      select: 'event_id,gross_income,tax_amount,net_income,payroll,other_expenses,profit',
      limit: '1',
    }, env, fetchImpl),
  ]);

  const event = events[0];
  if (!event) return null;

  const [eventTypes, regionCities, jobs, incomes, expenses] = await Promise.all([
    get('qpf_event_types', { id: `eq.${event.event_type_id}`, select: 'id,name', limit: '1' }, env, fetchImpl),
    event.region_city_id ? get('qpf_region_cities', { id: `eq.${event.region_city_id}`, select: 'id,name', limit: '1' }, env, fetchImpl) : Promise.resolve([]),
    get('qpf_event_jobs', {
      event_id: `eq.${eventId}`,
      status: 'eq.active',
      select: 'id,employee_id,role_id,rate_type,rate_amount,quantity,total_amount,started_at,ended_at,notes,created_at',
      order: 'created_at.asc',
    }, env, fetchImpl),
    get('qpf_incomes', {
      event_id: `eq.${eventId}`,
      status: 'eq.active',
      select: 'id,source_id,description,gross_amount,tax_enabled,tax_rate,tax_amount,net_amount,income_date,payment_method_id,created_at',
      order: 'income_date.desc',
    }, env, fetchImpl),
    get('qpf_expenses', {
      event_id: `eq.${eventId}`,
      status: 'eq.active',
      select: 'id,category_id,description,expense_kind,amount,expense_date,payment_method_id,paid_by_employee_id,reimbursement_status,created_at',
      order: 'expense_date.desc',
    }, env, fetchImpl),
  ]);

  const employeeIds = [...new Set(jobs.map((x) => x.employee_id))];
  const roleIds = [...new Set(jobs.map((x) => x.role_id))];
  const jobIds = jobs.map((x) => x.id);
  const sourceIds = [...new Set(incomes.map((x) => x.source_id).filter(Boolean))];
  const categoryIds = [...new Set(expenses.map((x) => x.category_id).filter(Boolean))];
  const paymentMethodIds = [...new Set([...incomes, ...expenses].map((x) => x.payment_method_id).filter(Boolean))];

  const [employees, roles, jobDutyLinks, sources, categories, paymentMethods] = await Promise.all([
    employeeIds.length ? get('qpf_employees', { id: inFilter(employeeIds), select: 'id,full_name' }, env, fetchImpl) : [],
    roleIds.length ? get('qpf_roles', { id: inFilter(roleIds), select: 'id,name' }, env, fetchImpl) : [],
    jobIds.length ? get('qpf_event_job_duties', { event_job_id: inFilter(jobIds), select: 'event_job_id,duty_id' }, env, fetchImpl) : [],
    sourceIds.length ? get('qpf_income_sources', { id: inFilter(sourceIds), select: 'id,name' }, env, fetchImpl) : [],
    categoryIds.length ? get('qpf_expense_categories', { id: inFilter(categoryIds), select: 'id,name' }, env, fetchImpl) : [],
    paymentMethodIds.length ? get('qpf_payment_methods', { id: inFilter(paymentMethodIds), select: 'id,name' }, env, fetchImpl) : [],
  ]);

  const dutyIds = [...new Set(jobDutyLinks.map((x) => x.duty_id))];
  const duties = dutyIds.length ? await get('qpf_duties', { id: inFilter(dutyIds), select: 'id,name' }, env, fetchImpl) : [];

  const employeeById = new Map(employees.map((x) => [x.id, x.full_name]));
  const roleById = new Map(roles.map((x) => [x.id, x.name]));
  const dutyById = new Map(duties.map((x) => [x.id, x.name]));
  const sourceById = new Map(sources.map((x) => [x.id, x.name]));
  const categoryById = new Map(categories.map((x) => [x.id, x.name]));
  const methodById = new Map(paymentMethods.map((x) => [x.id, x.name]));
  const dutiesByJob = new Map();
  for (const link of jobDutyLinks) {
    const list = dutiesByJob.get(link.event_job_id) ?? [];
    const name = dutyById.get(link.duty_id);
    if (name) list.push(name);
    dutiesByJob.set(link.event_job_id, list);
  }

  const financials = financialRows[0] ?? {};
  return {
    event: {
      id: event.id,
      title: event.title,
      eventType: eventTypes[0]?.name ?? null,
      unitCode: event.unit_code,
      regionCity: regionCities[0]?.name ?? null,
      eventDate: event.event_date,
      startTime: event.start_time,
      endTime: event.end_time,
      venue: event.venue,
      status: event.status,
      notes: event.notes,
    },
    financials: {
      grossIncome: number(financials.gross_income),
      tax: number(financials.tax_amount),
      netIncome: number(financials.net_income),
      payroll: number(financials.payroll),
      expenses: number(financials.other_expenses),
      profit: number(financials.profit),
    },
    jobs: jobs.map((job) => ({
      id: job.id,
      employeeId: job.employee_id,
      employeeName: employeeById.get(job.employee_id) ?? null,
      roleId: job.role_id,
      roleName: roleById.get(job.role_id) ?? null,
      rateType: job.rate_type,
      rateAmount: number(job.rate_amount),
      quantity: number(job.quantity),
      totalAmount: number(job.total_amount),
      startedAt: job.started_at,
      endedAt: job.ended_at,
      notes: job.notes,
      duties: dutiesByJob.get(job.id) ?? [],
    })),
    incomes: incomes.map((row) => ({
      id: row.id,
      source: sourceById.get(row.source_id) ?? null,
      description: row.description,
      grossAmount: number(row.gross_amount),
      taxEnabled: row.tax_enabled,
      taxRate: number(row.tax_rate),
      tax: number(row.tax_amount),
      netAmount: number(row.net_amount),
      incomeDate: row.income_date,
      paymentMethod: methodById.get(row.payment_method_id) ?? null,
    })),
    expenses: expenses.map((row) => ({
      id: row.id,
      category: categoryById.get(row.category_id) ?? null,
      description: row.description,
      expenseKind: row.expense_kind,
      amount: number(row.amount),
      expenseDate: row.expense_date,
      reimbursementStatus: row.reimbursement_status,
      paymentMethod: methodById.get(row.payment_method_id) ?? null,
    })),
  };
}
