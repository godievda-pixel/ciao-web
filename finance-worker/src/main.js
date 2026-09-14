import { validateTelegramInitData } from './telegram.js';
import {
  findActiveAdminByTelegramId,
  getDashboardSummary,
  listEmployeesWithBalances,
  listEventsWithFinancials,
} from './supabase.js';
import { createWorker } from './worker.js';

const app = createWorker({
  validateInitData: validateTelegramInitData,
  findAdmin: (telegramId, env) => findActiveAdminByTelegramId(telegramId, env),
  getDashboard: (query, env) => getDashboardSummary(query, env),
  listEmployees: (env) => listEmployeesWithBalances(env),
  listEvents: (query, env) => listEventsWithFinancials(query, env),
});

export default app;
