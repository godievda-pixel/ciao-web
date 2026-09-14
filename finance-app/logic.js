export function formatMoney(value) {
  return `${new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(Number(value || 0))} ₽`;
}

export function unitAccent(unit) {
  return ({ moscow:'#E7072E', spb:'#0F52BA', regions:'#5B9EEC', staff:'#008A4C', all:'#008A4C' })[unit] || '#008A4C';
}

const emptyToNull = (v) => (v === '' || v === undefined ? null : v);
const asNumber = (v, fallback = null) => {
  if (v === '' || v === null || v === undefined) return fallback;
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
};

export function buildEmployeePayload(form) {
  return {
    fullName: form.fullName?.trim(),
    employeeType: form.employeeType,
    organizationRoleId: emptyToNull(form.organizationRoleId),
    phone: emptyToNull(form.phone?.trim()),
    telegramUsername: emptyToNull(form.telegramUsername?.trim()),
    notes: emptyToNull(form.notes?.trim()),
  };
}

export function buildIncomePayload(form) {
  return {
    eventId: emptyToNull(form.eventId),
    unitCode: form.unitCode,
    sourceId: emptyToNull(form.sourceId),
    description: emptyToNull(form.description?.trim()),
    grossAmount: asNumber(form.grossAmount, 0),
    taxEnabled: Boolean(form.taxEnabled),
    taxRate: asNumber(form.taxRate, 9),
    incomeDate: form.incomeDate,
    paymentMethodId: emptyToNull(form.paymentMethodId),
  };
}

export function buildExpensePayload(form) {
  const kind = form.expenseKind || 'organization';
  return {
    eventId: emptyToNull(form.eventId),
    unitCode: form.unitCode,
    categoryId: emptyToNull(form.categoryId),
    description: emptyToNull(form.description?.trim()),
    expenseKind: kind,
    amount: asNumber(form.amount, 0),
    expenseDate: form.expenseDate,
    paymentMethodId: emptyToNull(form.paymentMethodId),
    paidByEmployeeId: kind === 'employee_reimbursement' ? emptyToNull(form.paidByEmployeeId) : null,
    reimbursementStatus: kind === 'employee_reimbursement' ? 'pending' : 'not_applicable',
  };
}
