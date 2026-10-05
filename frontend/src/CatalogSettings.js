import React, { useState } from 'react';
const blankReason = { name: '', kind: 'both', active: true };
const blankPerson = { name: '', employee_code: '', sector: '', active: true };
const kindName = { entry: 'Entrada', exit: 'Salida', both: 'Entrada y salida' };
export default function CatalogSettings({ data, busy, save }) {
  const [reason, setReason] = useState(blankReason);
  const [reasonId, setReasonId] = useState(null);
  const [person, setPerson] = useState(blankPerson);
  const [personId, setPersonId] = useState(null);
  const resetReason = () => { setReason(blankReason); setReasonId(null); };
  const resetPerson = () => { setPerson(blankPerson); setPersonId(null); };
  return <>
    <section className="panel"><h2>Motivos de movimiento</h2>
      <form onSubmit={e => save(e, `/api/reasons${reasonId ? `/${reasonId}` : ''}`, reason, resetReason, reasonId ? 'put' : 'post')}>
        <label>Nombre del motivo<input required maxLength={120} disabled={busy} value={reason.name} onChange={e => setReason({ ...reason, name: e.target.value })} /></label>
        <label>Se aplica a<select disabled={busy} value={reason.kind} onChange={e => setReason({ ...reason, kind: e.target.value })}>{Object.entries(kindName).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        <label>Estado del motivo<select disabled={busy} value={String(reason.active)} onChange={e => setReason({ ...reason, active: e.target.value === 'true' })}><option value="true">Activo</option><option value="false">Inactivo</option></select></label>
        <button disabled={busy}>{reasonId ? 'Guardar motivo' : 'Crear motivo'}</button>{reasonId && <button type="button" className="secondary" onClick={resetReason} disabled={busy}>Cancelar edición</button>}
      </form><ul>{data.reasons.map(r => <li key={r.id}>{r.name}<small>{kindName[r.kind]} · {r.active ? 'Activo' : 'Inactivo'}</small><button className="secondary" disabled={busy} onClick={() => { setReasonId(r.id); setReason({ name: r.name, kind: r.kind, active: r.active }); }}>Editar motivo {r.name}</button></li>)}</ul>
    </section>
    <section className="panel"><h2>Responsables</h2><p className="muted">Personas a cargo del movimiento. Estos registros no son cuentas de acceso.</p>
      <form onSubmit={e => save(e, `/api/responsibles${personId ? `/${personId}` : ''}`, person, resetPerson, personId ? 'put' : 'post')}>
        <label>Nombre del responsable<input required maxLength={120} disabled={busy} value={person.name} onChange={e => setPerson({ ...person, name: e.target.value })} /></label>
        <label>Legajo<input required maxLength={64} disabled={busy} value={person.employee_code} onChange={e => setPerson({ ...person, employee_code: e.target.value })} /></label>
        <label>Sector<input maxLength={120} disabled={busy} value={person.sector} onChange={e => setPerson({ ...person, sector: e.target.value })} /></label>
        <label>Estado del responsable<select disabled={busy} value={String(person.active)} onChange={e => setPerson({ ...person, active: e.target.value === 'true' })}><option value="true">Activo</option><option value="false">Inactivo</option></select></label>
        <button disabled={busy}>{personId ? 'Guardar responsable' : 'Crear responsable'}</button>{personId && <button type="button" className="secondary" onClick={resetPerson} disabled={busy}>Cancelar edición</button>}
      </form><ul>{data.responsibles.map(r => <li key={r.id}>{r.name}<small>{r.employee_code} · {r.sector || 'Sin sector'} · {r.active ? 'Activo' : 'Inactivo'}</small><button className="secondary" disabled={busy} onClick={() => { setPersonId(r.id); setPerson({ name: r.name, employee_code: r.employee_code, sector: r.sector, active: r.active }); }}>Editar responsable {r.name}</button></li>)}</ul>
    </section>
  </>;
}
