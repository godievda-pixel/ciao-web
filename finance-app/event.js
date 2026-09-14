import { createApiClient } from './api.js';
import { formatMoney, unitAccent, buildIncomePayload, buildExpensePayload } from './logic.js';

const root = document.querySelector('#app');
const tg = window.Telegram?.WebApp;
try { tg?.ready(); tg?.expand(); tg?.setHeaderColor?.('#070809'); tg?.setBackgroundColor?.('#070809'); } catch {}

const eventId = new URLSearchParams(location.search).get('id');
const initData = tg?.initData || '';
const api = createApiClient({ initData });
const state = { admin:null, refs:null, employees:[], detail:null };
const unitNames = { moscow:'Москва', spb:'Петербург', regions:'Регионы', staff:'Штат' };
const statusNames = { planned:'Запланирован', completed:'Завершён', cancelled:'Отменён' };

function esc(v=''){return String(v).replace(/[&<>"']/g,(m)=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));}
function initials(name=''){return name.split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join('').toUpperCase()||'?';}
function today(){return new Date().toISOString().slice(0,10);}
function optionList(rows, valueKey='id', labelKey='name', selected=''){return `<option value="">—</option>${rows.map(x=>`<option value="${esc(x[valueKey])}" ${String(x[valueKey])===String(selected)?'selected':''}>${esc(x[labelKey])}</option>`).join('')}`;}
function formValue(form,name){const el=form.elements[name];return el?.type==='checkbox'?el.checked:el?.value;}
function errorText(e){const code=e?.message||'';return ({telegram_init_data_required:'Открой приложение из Telegram',telegram_auth_invalid:'Telegram-авторизация не прошла',admin_access_denied:'Нет доступа администратора',event_not_found:'Ивент не найден'}[code]||'Не удалось выполнить операцию');}
function toast(text){let el=document.querySelector('.toast');if(!el){el=document.createElement('div');el.className='toast';document.body.append(el);}el.textContent=text;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),1800);}
function showError(message){const el=document.querySelector('#sheetError');if(el){el.textContent=message;el.hidden=false;}else toast(message);}
function openSheet(title, body){closeSheet();const overlay=document.createElement('div');overlay.className='overlay show';overlay.id='overlay';overlay.onclick=closeSheet;const sheet=document.createElement('div');sheet.className='sheet open';sheet.id='sheet';sheet.innerHTML=`<div class="sheet-title">${title}</div><div id="sheetError" class="error" hidden></div>${body}`;document.body.append(overlay,sheet);sheet.querySelectorAll('[data-close]').forEach(x=>x.onclick=closeSheet);}
function closeSheet(){document.querySelector('#overlay')?.remove();document.querySelector('#sheet')?.remove();}
function formShell(fields, submitText='Сохранить'){return `<form id="dataForm">${fields}<div class="form-actions"><button type="button" class="btn" data-close>Отмена</button><button class="btn primary" type="submit">${submitText}</button></div></form>`;}

function render(){
  const d=state.detail;
  if(!d){root.innerHTML='<div class="boot"><div class="boot-logo">КВИЗ ПЛЮС</div><div class="boot-line"><i></i></div></div>';return;}
  const e=d.event, f=d.financials||{}, jobs=d.jobs||[], incomes=d.incomes||[], expenses=d.expenses||[];
  document.documentElement.style.setProperty('--accent',unitAccent(e.unitCode));
  root.innerHTML=`<div class="shell event-page">
    <header class="top"><div class="brand-row"><button class="back-link" id="backBtn">‹</button><div class="brand">КВИЗ ПЛЮС</div><div class="admin">${esc(state.admin?.displayName||'Админ')}</div></div><div class="title-row"><div><div class="eyebrow">${esc(e.eventType||'Ивент')} • ${esc(unitNames[e.unitCode]||e.unitCode)}</div><div class="page-title event-page-title">${esc(e.title)}</div></div><div class="period">${esc(e.eventDate)}</div></div><div class="event-meta-wide">${e.startTime?`${esc(e.startTime.slice(0,5))} • `:''}${e.venue?`${esc(e.venue)} • `:''}${e.regionCity?`${esc(e.regionCity)} • `:''}${esc(statusNames[e.status]||e.status)}</div></header>
    <main>
      <div class="hero"><div class="eyebrow">Чистая прибыль мероприятия</div><div class="hero-value">${formatMoney(f.profit)}</div><div class="hero-sub">после налога, ФОТ и прочих расходов</div></div>
      <div class="rule"></div>
      <div class="pnl-grid"><div class="pnl"><small>Валовый доход</small><b>${formatMoney(f.grossIncome)}</b><span>чистыми ${formatMoney(f.netIncome)}</span></div><div class="pnl"><small>Налог</small><b>${formatMoney(f.tax)}</b><span>по облагаемым доходам</span></div><div class="pnl"><small>ФОТ ивента</small><b>${formatMoney(f.payroll)}</b><span>${jobs.length} работ</span></div><div class="pnl"><small>Прочие расходы</small><b>${formatMoney(f.expenses)}</b><span>${expenses.length} операций</span></div></div>

      <div class="section-title">Команда</div><button class="primary-line" data-action="job">Добавить работу сотруднику <span>＋</span></button>
      <div>${jobs.length?jobs.map(renderJob).join(''):'<div class="empty">Сотрудники на ивент ещё не добавлены.</div>'}</div>

      <div class="section-title">Доходы</div><button class="primary-line" data-action="income">Добавить доход <span>＋</span></button>
      <div>${incomes.length?incomes.map(renderIncome).join(''):'<div class="empty">Доходов пока нет.</div>'}</div>

      <div class="section-title">Расходы</div><button class="primary-line" data-action="expense">Добавить расход <span>＋</span></button>
      <div>${expenses.length?expenses.map(renderExpense).join(''):'<div class="empty">Расходов пока нет.</div>'}</div>
    </main>
    <div class="event-bottom-actions"><button class="btn" data-action="income">＋ Доход</button><button class="btn primary" data-action="job">＋ Работа</button></div>
  </div>`;
  bind();
}

function renderJob(j){return `<div class="event-job"><div class="person"><div class="avatar">${initials(j.employeeName)}</div><div class="person-main"><div class="person-name">${esc(j.employeeName||'Сотрудник')}</div><div class="person-meta">${esc(j.roleName||'Роль')} • ${j.rateType==='hourly'?`${j.quantity} ч × ${formatMoney(j.rateAmount)}`:formatMoney(j.rateAmount)}</div></div><div class="balance"><b>${formatMoney(j.totalAmount)}</b><span>начислено</span></div></div>${j.duties?.length?`<div class="duty-list">${j.duties.map(x=>`<span>${esc(x)}</span>`).join('')}</div>`:''}${j.notes?`<div class="role-note">${esc(j.notes)}</div>`:''}<div class="row-actions"><button class="mini-danger" data-annul-type="event_job" data-annul-id="${esc(j.id)}">Аннулировать</button></div></div>`;}
function renderIncome(x){return `<div class="operation"><div><b>${esc(x.source||x.description||'Доход')}</b><span>${esc(x.incomeDate)}${x.paymentMethod?` • ${esc(x.paymentMethod)}`:''}${x.taxEnabled?` • налог ${x.taxRate}%`:''}</span></div><div class="operation-value"><strong class="profit">+${formatMoney(x.grossAmount)}</strong><button class="mini-danger" data-annul-type="income" data-annul-id="${esc(x.id)}">Аннулировать</button></div></div>`;}
function renderExpense(x){return `<div class="operation"><div><b>${esc(x.category||x.description||'Расход')}</b><span>${esc(x.expenseDate)}${x.paymentMethod?` • ${esc(x.paymentMethod)}`:''}${x.expenseKind==='employee_reimbursement'?` • компенсация`:''}</span></div><div class="operation-value"><strong class="advance">−${formatMoney(x.amount)}</strong><button class="mini-danger" data-annul-type="expense" data-annul-id="${esc(x.id)}">Аннулировать</button></div></div>`;}

function bind(){
  document.querySelector('#backBtn').onclick=()=>location.href='/';
  document.querySelectorAll('[data-action]').forEach(btn=>btn.onclick=()=>{
    if(btn.dataset.action==='job')jobForm();
    if(btn.dataset.action==='income')incomeForm();
    if(btn.dataset.action==='expense')expenseForm();
  });
  document.querySelectorAll('[data-annul-id]').forEach(btn=>btn.onclick=()=>annulForm(btn.dataset.annulType,btn.dataset.annulId));
}

async function reload(){state.detail=await api.get(`/api/qpf/events/${encodeURIComponent(eventId)}`);state.employees=await api.get('/api/qpf/employees');render();}

function jobForm(){
  const roles=(state.refs?.roles||[]).filter(r=>r.scope==='event'||r.scope==='both');
  const duties=state.refs?.duties||[];
  openSheet('Работа на ивенте',formShell(`<div class="field"><label>Сотрудник</label><select name="employeeId" required>${optionList(state.employees,'id','fullName')}</select></div><div class="field"><label>Роль</label><select name="roleId" required>${optionList(roles)}</select></div><div class="field-row"><div class="field"><label>Тип ставки</label><select name="rateType"><option value="per_event">За квиз</option><option value="hourly">Почасовая</option><option value="fixed">Разовая сумма</option></select></div><div class="field"><label>Ставка</label><input type="number" min="0" step="0.01" name="rateAmount" required></div></div><div class="field-row"><div class="field"><label>Количество / часы</label><input type="number" min="0.25" step="0.25" name="quantity" value="1" required></div><div class="field"><label>Начало</label><input type="time" name="startedAt"></div></div><div class="field"><label>Окончание</label><input type="time" name="endedAt"></div><div class="field"><label>Обязанности</label><div class="duty-options">${duties.map(d=>`<label class="check"><input type="checkbox" name="dutyIds" value="${esc(d.id)}"> ${esc(d.name)}</label>`).join('')}</div></div><div class="field"><label>Комментарий</label><textarea name="notes"></textarea></div>`,'Добавить работу'));
  const f=document.querySelector('#dataForm');
  const roleSelect=f.elements.roleId, rateType=f.elements.rateType, rateAmount=f.elements.rateAmount, quantity=f.elements.quantity;
  roleSelect.onchange=()=>{const role=roles.find(r=>r.id===roleSelect.value);if(role?.defaultRateType)rateType.value=role.defaultRateType;if(role?.defaultRate!=null)rateAmount.value=role.defaultRate;quantity.value='1';};
  rateType.onchange=()=>{if(rateType.value!=='hourly')quantity.value='1';};
  f.onsubmit=async ev=>{ev.preventDefault();const dutyIds=[...f.querySelectorAll('input[name="dutyIds"]:checked')].map(x=>x.value);try{await api.post('/api/qpf/event-jobs',{eventId,employeeId:formValue(f,'employeeId'),roleId:formValue(f,'roleId'),rateType:formValue(f,'rateType'),rateAmount:Number(formValue(f,'rateAmount')),quantity:Number(formValue(f,'quantity')),startedAt:formValue(f,'startedAt')||null,endedAt:formValue(f,'endedAt')||null,notes:formValue(f,'notes')||null,dutyIds});closeSheet();toast('Работа добавлена');await reload();}catch(err){showError(errorText(err));}};
}

function incomeForm(){
  const refs=state.refs||{}; const e=state.detail.event;
  openSheet('Доход ивента',formShell(`<div class="field"><label>Сумма</label><input type="number" min="0" step="0.01" name="grossAmount" required></div><div class="field"><label>Источник</label><select name="sourceId">${optionList(refs.incomeSources||[])}</select></div><div class="field-row"><div class="field"><label>Дата</label><input type="date" name="incomeDate" value="${e.eventDate||today()}" required></div><div class="field"><label>Способ оплаты</label><select name="paymentMethodId">${optionList(refs.paymentMethods||[])}</select></div></div><div class="field-row"><label class="check"><input type="checkbox" name="taxEnabled" checked> Учитывать налог</label><div class="field"><label>Ставка, %</label><input type="number" name="taxRate" value="9" step="0.01"></div></div><div class="field"><label>Комментарий</label><textarea name="description"></textarea></div>`,'Добавить доход'));
  document.querySelector('#dataForm').onsubmit=async ev=>{ev.preventDefault();const f=ev.currentTarget;try{await api.post('/api/qpf/incomes',buildIncomePayload({eventId,unitCode:e.unitCode,sourceId:formValue(f,'sourceId'),description:formValue(f,'description'),grossAmount:formValue(f,'grossAmount'),taxEnabled:formValue(f,'taxEnabled'),taxRate:formValue(f,'taxRate'),incomeDate:formValue(f,'incomeDate'),paymentMethodId:formValue(f,'paymentMethodId')}));closeSheet();toast('Доход добавлен');await reload();}catch(err){showError(errorText(err));}};
}

function expenseForm(){
  const refs=state.refs||{}; const e=state.detail.event;
  openSheet('Расход ивента',formShell(`<div class="field"><label>Сумма</label><input type="number" min="0" step="0.01" name="amount" required></div><div class="field"><label>Категория</label><select name="categoryId">${optionList(refs.expenseCategories||[])}</select></div><div class="field"><label>Тип расхода</label><select name="expenseKind"><option value="organization">Расход организации</option><option value="employee_reimbursement">Оплатил сотрудник — компенсировать</option></select></div><div class="field"><label>Сотрудник для компенсации</label><select name="paidByEmployeeId">${optionList(state.employees,'id','fullName')}</select></div><div class="field-row"><div class="field"><label>Дата</label><input type="date" name="expenseDate" value="${e.eventDate||today()}" required></div><div class="field"><label>Способ оплаты</label><select name="paymentMethodId">${optionList(refs.paymentMethods||[])}</select></div></div><div class="field"><label>Комментарий</label><textarea name="description"></textarea></div>`,'Добавить расход'));
  document.querySelector('#dataForm').onsubmit=async ev=>{ev.preventDefault();const f=ev.currentTarget;const kind=formValue(f,'expenseKind');if(kind==='employee_reimbursement'&&!formValue(f,'paidByEmployeeId'))return showError('Выбери сотрудника для компенсации');try{await api.post('/api/qpf/expenses',buildExpensePayload({eventId,unitCode:e.unitCode,categoryId:formValue(f,'categoryId'),description:formValue(f,'description'),expenseKind:kind,amount:formValue(f,'amount'),expenseDate:formValue(f,'expenseDate'),paymentMethodId:formValue(f,'paymentMethodId'),paidByEmployeeId:formValue(f,'paidByEmployeeId')}));closeSheet();toast('Расход добавлен');await reload();}catch(err){showError(errorText(err));}};
}

function annulForm(entityType, entityId){
  openSheet('Аннулировать запись',formShell(`<div class="field"><label>Причина аннулирования</label><textarea name="reason" required placeholder="Комментарий обязателен"></textarea></div><div class="role-note">Запись останется в истории, но перестанет участвовать в расчётах.</div>`,'Аннулировать'));
  document.querySelector('#dataForm').onsubmit=async ev=>{ev.preventDefault();const f=ev.currentTarget;const reason=formValue(f,'reason')?.trim();if(!reason)return showError('Укажи причину аннулирования');try{await api.post('/api/qpf/annul',{entityType,entityId,reason});closeSheet();toast('Запись аннулирована');await reload();}catch(err){showError(errorText(err));}};
}

async function bootstrap(){
  if(!initData){root.innerHTML='<div class="gate"><div><b>Квиз Плюс • Финансы</b><p>Открой страницу ивента из Telegram Mini App.</p></div></div>';return;}
  if(!eventId){root.innerHTML='<div class="gate"><div><b>Ивент не выбран</b><p>Вернись к списку мероприятий.</p></div></div>';return;}
  try{
    const session=await api.post('/api/qpf/session',{});
    state.admin=session.admin||session;
    const [refs,employees,detail]=await Promise.all([api.get('/api/qpf/references'),api.get('/api/qpf/employees'),api.get(`/api/qpf/events/${encodeURIComponent(eventId)}`)]);
    state.refs=refs;state.employees=employees;state.detail=detail;render();
  }catch(e){root.innerHTML=`<div class="gate"><div><b>Доступ закрыт</b><p>${esc(errorText(e))}</p></div></div>`;}
}
bootstrap();
