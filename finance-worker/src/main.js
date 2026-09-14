import { validateTelegramInitData } from './telegram.js';
import { findActiveAdminByTelegramId } from './supabase.js';
import { createWorker } from './worker.js';

const app = createWorker({
  validateInitData: validateTelegramInitData,
  findAdmin: findActiveAdminByTelegramId,
});

export default app;
