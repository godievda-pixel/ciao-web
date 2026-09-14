function headers(env, admin) {
  return {
    apikey: env.SUPABASE_SERVICE_ROLE_KEY,
    authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
    accept: 'application/json',
    'content-type': 'application/json',
    prefer: 'return=representation',
    'x-qpf-admin-id': admin.id,
    'x-qpf-source': 'app',
  };
}

export async function createEventJobWithDuties(payload, env, admin, fetchImpl = fetch) {
  const url = new URL('/rest/v1/rpc/qpf_create_event_job', env.SUPABASE_URL);
  const response = await fetchImpl(url, {
    method: 'POST',
    headers: headers(env, admin),
    body: JSON.stringify({
      p_event_id: payload.eventId,
      p_employee_id: payload.employeeId,
      p_role_id: payload.roleId,
      p_rate_type: payload.rateType,
      p_rate_amount: payload.rateAmount,
      p_quantity: payload.quantity ?? 1,
      p_started_at: payload.startedAt ?? null,
      p_ended_at: payload.endedAt ?? null,
      p_notes: payload.notes ?? null,
      p_duty_ids: Array.isArray(payload.dutyIds) ? payload.dutyIds : [],
      p_created_by: admin.id,
    }),
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => '');
    throw new Error(`qpf_create_event_job_failed:${response.status}:${detail}`);
  }
  return response.json();
}
