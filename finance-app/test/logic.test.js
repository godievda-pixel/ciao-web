import test from 'node:test';
import assert from 'node:assert/strict';
import { formatMoney, unitAccent, buildEmployeePayload, buildIncomePayload, buildExpensePayload } from '../logic.js';

test('formats whole ruble amounts', () => {
  assert.equal(formatMoney(124000), '124 000 ₽');
});

test('uses Quiz Plus identity accents for each unit', () => {
  assert.equal(unitAccent('moscow'), '#E7072E');
  assert.equal(unitAccent('spb'), '#0F52BA');
  assert.equal(unitAccent('regions'), '#5B9EEC');
  assert.equal(unitAccent('staff'), '#008A4C');
});

test('normalizes employee optional fields', () => {
  assert.deepEqual(buildEmployeePayload({ fullName:'Иван', employeeType:'both', organizationRoleId:'', phone:'', telegramUsername:'@ivan', notes:'' }), {
    fullName:'Иван', employeeType:'both', organizationRoleId:null, phone:null, telegramUsername:'@ivan', notes:null,
  });
});

test('defaults enabled income tax to 9 percent', () => {
  const value = buildIncomePayload({ unitCode:'moscow', grossAmount:'100000', taxEnabled:true, taxRate:'', incomeDate:'2026-09-14' });
  assert.equal(value.grossAmount, 100000);
  assert.equal(value.taxRate, 9);
});

test('marks employee-paid expense as pending reimbursement', () => {
  const value = buildExpensePayload({ unitCode:'moscow', amount:'3500', expenseDate:'2026-09-14', paidByEmployeeId:'e1', expenseKind:'employee_reimbursement' });
  assert.equal(value.reimbursementStatus, 'pending');
  assert.equal(value.paidByEmployeeId, 'e1');
});
