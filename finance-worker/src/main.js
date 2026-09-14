import { validateTelegramInitData } from './telegram.js';
import {
  findActiveAdminByTelegramId,
  getDashboardSummary,
  listEmployeesWithBalances,
  listEventsWithFinancials,
} from './supabase.js';
import { listReferences } from './references.js';
import {
  createEmployee,
  createEvent,
  createEventJob,
  createIncome,
  createExpense,
  createAccrual,
  createPayment,
  annulEntity,
} from './mutations.js';
import { createWorker } from './worker.js';

const app = createWorker({
  validateInitData: validateTelegramInitData,
  findAdmin: (telegramId, env) => findActiveAdminByTelegramId(telegramId, env),
  getDashboard: (query, env) => getDashboardSummary(query, env),
  listEmployees: (env) => listEmployeesWithBalances(env),
  listEvents: (query, env) => listEventsWithFinancials(query, env),
  listReferences: (env) => listReferences(env),
  createEmployee: (payload, env, admin) => createEmployee(payload, env, admin),
  createEvent: (payload, env, admin) => createEvent(payload, env, admin),
  createEventJob: (payload, env, admin) => createEventJob(payload, env, admin),
  createIncome: (payload, env, admin) => createIncome(payload, env, admin),
  createExpense: (payload, env, admin) => createExpense(payload, env, admin),
  createAccrual: (payload, env, admin) => createAccrual(payload, env, admin),
  createPayment: (payload, env, admin) => createPayment(payload, env, admin),
  annulEntity: (payload, env, admin) => annulEntity(payload, env, admin),
});

export default app;
