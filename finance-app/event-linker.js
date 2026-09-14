import { createApiClient } from './api.js';

const initData = window.Telegram?.WebApp?.initData || '';
const api = createApiClient({ initData });
let busy = false;

document.addEventListener('click', async (event) => {
  const card = event.target.closest('.event');
  if (!card || busy) return;
  const activeUnit = document.querySelector('.unit-btn.active')?.dataset.unit;
  if (!activeUnit || activeUnit === 'staff') return;
  const cards = [...document.querySelectorAll('.event')];
  const index = cards.indexOf(card);
  if (index < 0) return;
  busy = true;
  try {
    const events = await api.get(`/api/qpf/events?unit=${encodeURIComponent(activeUnit)}`);
    const row = events[index];
    if (row?.id) window.location.href = `/event.html?id=${encodeURIComponent(row.id)}`;
  } finally {
    busy = false;
  }
});
