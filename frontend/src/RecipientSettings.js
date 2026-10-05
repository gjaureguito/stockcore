import React, { useState } from 'react';
const blankCompany = { name: '', active: true };
const blankRecipient = { name: '', company_id: '', active: true };
export default function RecipientSettings({ data, busy, save }) {
  const [company, setCompany] = useState(blankCompany);
  const [companyId, setCompanyId] = useState(null);
  const [recipient, setRecipient] = useState(blankRecipient);
  const [recipientId, setRecipientId] = useState(null);
  const resetCompany = () => { setCompany(blankCompany); setCompanyId(null); };
  const resetRecipient = () => { setRecipient(blankRecipient); setRecipientId(null); };
  return <>
    <section className="panel"><h2>Empresas externas</h2><form onSubmit={e => save(e, `/api/recipient-companies${companyId ? `/${companyId}` : ''}`, company, resetCompany, companyId ? 'put' : 'post')}>
      <label>Nombre de empresa externa<input required disabled={busy} maxLength={120} value={company.name} onChange={e => setCompany({ ...company, name: e.target.value })} /></label>
      <label>Estado de empresa externa<select disabled={busy} value={String(company.active)} onChange={e => setCompany({ ...company, active: e.target.value === 'true' })}><option value="true">Activa</option><option value="false">Inactiva</option></select></label>
      <button disabled={busy}>{companyId ? 'Guardar empresa externa' : 'Crear empresa externa'}</button>{companyId && <button type="button" disabled={busy} className="secondary" onClick={resetCompany}>Cancelar edición de empresa</button>}
    </form><ul>{data.recipient_companies.map(c => <li key={c.id}>{c.name}<small>{c.active ? 'Activa' : 'Inactiva'}</small><button disabled={busy} className="secondary" onClick={() => { setCompanyId(c.id); setCompany({ name: c.name, active: c.active }); }}>Editar empresa {c.name}</button></li>)}</ul></section>
    <section className="panel"><h2>Destinatarios / retirantes</h2><form onSubmit={e => save(e, `/api/recipients${recipientId ? `/${recipientId}` : ''}`, { ...recipient, company_id: recipient.company_id ? Number(recipient.company_id) : null }, resetRecipient, recipientId ? 'put' : 'post')}>
      <label>Nombre del retirante<input required disabled={busy} maxLength={120} value={recipient.name} onChange={e => setRecipient({ ...recipient, name: e.target.value })} /></label>
      <label>Empresa del retirante<select disabled={busy} value={recipient.company_id || ''} onChange={e => setRecipient({ ...recipient, company_id: e.target.value })}><option value="">Nuestra empresa · {data.company.name}</option>{data.recipient_companies.map(c => <option key={c.id} value={c.id}>{c.name}{!c.active ? ' (inactiva)' : ''}</option>)}</select></label>
      <label>Estado del retirante<select disabled={busy} value={String(recipient.active)} onChange={e => setRecipient({ ...recipient, active: e.target.value === 'true' })}><option value="true">Activo</option><option value="false">Inactivo</option></select></label>
      <button disabled={busy}>{recipientId ? 'Guardar retirante' : 'Crear retirante'}</button>{recipientId && <button type="button" disabled={busy} className="secondary" onClick={resetRecipient}>Cancelar edición de retirante</button>}
    </form><ul>{data.recipients.map(r => <li key={r.id}>{r.name}<small>{r.company_id ? data.recipient_companies.find(c => c.id === r.company_id)?.name : data.company.name} · {r.active ? 'Activo' : 'Inactivo'}</small><button disabled={busy} className="secondary" onClick={() => { setRecipientId(r.id); setRecipient({ name: r.name, company_id: r.company_id || '', active: r.active }); }}>Editar retirante {r.name}</button></li>)}</ul></section>
  </>;
}
