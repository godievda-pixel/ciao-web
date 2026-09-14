function serviceHeaders(env) {
  return {
    apikey: env.SUPABASE_SERVICE_ROLE_KEY,
    authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
    accept: 'application/json',
  };
}

async function supabaseGet(table, params, env, fetchImpl = fetch) {
  const url = new URL(`/rest/v1/${table}`, env.SUPABASE_URL);
  for (const [key, value] of Object.entries(params)) {
    if (Array.isArray(value)) {
      for (const item of value) {
        if (item !== undefined && item !== null && item !== '') url.searchParams.append(key, item);
      }
    } else if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value);
    }
  }
  const response = await fetchImpl(url, { headers: serviceHeaders(env) });
  if (!response.ok) {
    throw new Error(`supabase_${table}_failed:${response.status}`);
  }
  return response.json();
}

function number(value) {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

function sum(rows, key) {
  return rows.reduce((total, row) => total + number(row[key]), 0);
}

function monthBounds(month) {
  if (!/^\d{4}-\d{2}$/.test(month ?? '')) {
    throw new Error('invalid_month');
  }
  const [year, monthNumber] = month.split('-').map(Number);
  if (monthNumber < 1 || monthNumber > 12) throw new Error('invalid_month');
  const start = `${year}-${String(monthNumber).padStart(2, '0')}-01`;
  const next = new Date(Date.UTC(year, monthNumber, 1));
  const end = `${next.getUTCFullYear()}-${String(next.getUTCMonth() + 1).padStart(2, '0')}-01`;
  return { start, end };
}

export async function findActiveAdminByTelegramId(telegramId, env, fetchImpl = fetch) {
  const rows = await supabaseGet('qpf_admins', {
    telegram_id: `eq.${telegramId}`,
    is_active: 'eq.true',
    select: 'id,telegram_id,display_name,is_active',
    limit: '1',
  }, env, fetchImpl);
  return rows[0] ?? null;
}

export async function getDashboardSummary({ month, unit }, env, fetchImpl = fetch) {
  const { start, end } = monthBounds(month);
  const unitFilter = unit && unit !== 'all' ? `eq.${unit}` : null;

  const [incomes, expenses, accruals, balances] = await Promise.all([
    supabaseGet('qpf_incomes', {
      select: 'gross_amount,tax_amount,net_amount',
      status: 'eq.active',
      income_date: [`gte.${start}`, `lt.${end}`],
      unit_code: unitFilter,
    }, env, fetchImpl),
    supabaseGet('qpf_expenses', {
      select: 'amount',
      status: 'eq.active',
      expense_date: [`gte.${start}`, `lt.${end}`],
      unit_code: unitFilter,
    }, env, fetchImpl),
    supabaseGet('qpf_accruals', {
      select: 'amount,accrual_type',
      status: 'eq.active',
      accrued_on: [`gte.${start}`, `lt.${end}`],
      accrual_type: 'neq.reimbursement',
      unit_code: unitFilter,
    }, env, fetchImpl),
    supabaseGet('qpf_employee_balances', {
      select: 'balance_due',
    }, env, fetchImpl),
  ]);

  const grossIncome = sum(incomes, 'gross_amount');
  const tax = sum(incomes, 'tax_amount');
  const netIncome = sum(incomes, 'net_amount');
  const payroll = sum(accruals, 'amount');
  const expenseTotal = sum(expenses, 'amount');
  const toPay = balances.reduce((total, row) => total + Math.max(number(row.balance_due), 0), 0);

  return {
    grossIncome,
    tax,
    netIncome,
    payroll,
    expenses: expenseTotal,
    profit: netIncome - payroll - expenseTotal,
    toPay,
  };
}

export async function listEmployeesWithBalances(env, fetchImpl = fetch) {
  const [employees, balances, roles] = await Promise.all([
    supabaseGet('qpf_employees', {
      select: 'id,full_name,employee_type,organization_role_id,telegram_username,is_active',
      order: 'full_name.asc',
    }, env, fetchImpl),
    supabaseGet('qpf_employee_balances', {
      select: 'employee_id,total_accrued,total_paid,balance_due',
    }, env, fetchImpl),
    supabaseGet('qpf_roles', {
      select: 'id,name',
      role_scope: 'in.(organization,both)',
    }, env, fetchImpl),
  ]);

  const balanceByEmployee = new Map(balances.map((row) => [row.employee_id, row]));
  const roleById = new Map(roles.map((row) => [row.id, row.name]));

  return employees.map((employee) => {
    const balance = balanceByEmployee.get(employee.id) ?? {};
    return {
      id: employee.id,
      fullName: employee.full_name,
      employeeType: employee.employee_type,
      organizationRole: roleById.get(employee.organization_role_id) ?? null,
      telegramUsername: employee.telegram_username,
      isActive: employee.is_active,
      totalAccrued: number(balance.total_accrued),
      totalPaid: number(balance.total_paid),
      balanceDue: number(balance.balance_due),
    };
  });
}

export async function listEventsWithFinancials({ unit, from, to }, env, fetchImpl = fetch) {
  const rows = await supabaseGet('qpf_event_financials', {
    select: 'event_id,title,event_date,unit_code,gross_income,tax_amount,net_income,payroll,other_expenses,profit',
    unit_code: unit && unit !== 'all' ? `eq.${unit}` : null,
    event_date: [from ? `gte.${from}` : null, to ? `lte.${to}` : null],
    order: 'event_date.desc',
  }, env, fetchImpl);

  return rows.map((row) => ({
    id: row.event_id,
    title: row.title,
    eventDate: row.event_date,
    unitCode: row.unit_code,
    grossIncome: number(row.gross_income),
    tax: number(row.tax_amount),
    netIncome: number(row.net_income),
    payroll: number(row.payroll),
    expenses: number(row.other_expenses),
    profit: number(row.profit),
  }));
}
