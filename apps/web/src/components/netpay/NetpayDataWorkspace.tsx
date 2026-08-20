import { ChangeEvent, useEffect, useState } from 'react';
import { apiErrorMessage, netpayApi, newIdempotencyKey, type NetpayApiClient, type OperationalDataBatch } from '../../api/netpay';

const labels: Record<string, string> = {
  monthly_store_profitability: 'Rentabilidad', no_usage_campaign: 'No uso', needs_review: 'Requiere revisión', accepted: 'Importado', rejected: 'Rechazado',
  valid: 'Válida', invalid: 'Inválida', matched: 'Vinculada', unmatched: 'Sin vínculo', ambiguous: 'Ambigua', insert: 'Insert', update: 'Update', unchanged: 'Sin cambio', conflict: 'Conflicto',
};
const label = (value?: string | null) => value ? labels[value] || value : 'No disponible';
const errorLabels: Record<string, string> = { missing_store_id: 'Falta Store ID', invalid_store_id: 'Store ID inválido', missing_reporting_period: 'Falta periodo', invalid_profitability: 'Rentabilidad inválida', invalid_months_without_usage: 'Meses sin uso inválidos', duplicate_row: 'Fila duplicada', client_reference_unmatched: 'Client ID no encontrado' };

export function NetpayDataWorkspace({ client = netpayApi }: { client?: NetpayApiClient }) {
  const [tab, setTab] = useState<'import' | 'profitability' | 'no_use' | 'history'>('import');
  const [datasetType, setDatasetType] = useState('monthly_store_profitability');
  const [file, setFile] = useState<File | null>(null);
  const [rfc, setRfc] = useState('');
  const [batches, setBatches] = useState<OperationalDataBatch[]>([]);
  const [current, setCurrent] = useState<OperationalDataBatch | null>(null);
  const [results, setResults] = useState<Record<string, unknown>[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function load() { try { const page = await client.listOperationalDatasets(); setBatches(page.items); } catch (reason) { setError(apiErrorMessage(reason)); } }
  useEffect(() => { void load(); }, []);
  async function upload() {
    if (!file) { setError('Selecciona un archivo XLSX o CSV.'); return; }
    setBusy(true); setError(''); setNotice('');
    try {
      const batch = await client.uploadOperationalDataset(file, datasetType, datasetType === 'no_usage_campaign' ? rfc : '', newIdempotencyKey());
      setCurrent(batch);
      if (batch.duplicate_upload && batch.status === 'rejected') setNotice('Este archivo ya fue rechazado. Carga una versión corregida para crear un batch nuevo.');
      else if (batch.duplicate_upload) setNotice('Este archivo ya existe. Se recuperó el batch idempotente sin duplicarlo.');
      await load();
    } catch (reason) { setError(apiErrorMessage(reason)); } finally { setBusy(false); }
  }
  async function operate(action: 'accept' | 'reject') {
    if (!current) return;
    setBusy(true); setError('');
    try {
      const batch = action === 'accept' ? await client.acceptOperationalDataset(current.id, current.preview_token, newIdempotencyKey()) : await client.rejectOperationalDataset(current.id, newIdempotencyKey());
      setCurrent(batch);
      if (batch.status === 'accepted') setResults(await client.getOperationalDatasetResults(batch.id));
      await load();
    } catch (reason) { setError(apiErrorMessage(reason)); } finally { setBusy(false); }
  }
  async function resolve(rowId: string, storeReferenceId: string) { if (!current || !storeReferenceId) return; setBusy(true); setError(''); try { setCurrent(await client.resolveOperationalRow(current.id, rowId, storeReferenceId, newIdempotencyKey())); } catch (reason) { setError(apiErrorMessage(reason)); } finally { setBusy(false); } }
  async function open(batch: OperationalDataBatch) { setBusy(true); setError(''); setNotice(''); try { const detail = await client.getOperationalDataset(batch.id); setCurrent(detail); setResults(detail.status === 'accepted' ? await client.getOperationalDatasetResults(detail.id) : []); setTab(detail.dataset_type === 'monthly_store_profitability' && detail.status === 'accepted' ? 'profitability' : detail.dataset_type === 'no_usage_campaign' && detail.status === 'accepted' ? 'no_use' : 'import'); } catch (reason) { setError(apiErrorMessage(reason)); } finally { setBusy(false); } }

  return <section className="netpay-workspace">
    <header className="netpay-hero"><div><p className="eyebrow">OPERACIÓN ASISTIDA</p><h1>Datos Netpay</h1><p>Preview determinístico y confirmación humana antes de importar.</p><small>Organización: {client.runtime.organizationLabel || client.runtime.organizationSelector}</small></div></header>
    <nav aria-label="Secciones de Datos Netpay"><button onClick={() => setTab('import')}>Importar XLSX</button><button onClick={() => setTab('profitability')}>Rentabilidad</button><button onClick={() => setTab('no_use')}>No uso</button><button onClick={() => setTab('history')}>Historial de importaciones</button></nav>
    {error && <p role="alert" className="error-panel">{error}</p>}{notice && <p role="status" className="radar-notice">{notice}</p>}
    {tab === 'import' && <><section className="mutation-panel"><h2>Importar archivo</h2><label>Tipo de dataset<select value={datasetType} onChange={(event) => { setDatasetType(event.target.value); setRfc(''); }}><option value="monthly_store_profitability">Rentabilidad mensual</option><option value="no_usage_campaign">Comercios en no uso</option></select></label>{datasetType === 'no_usage_campaign' && <label>RFC de distribuidor (filtro efímero)<input value={rfc} onChange={(event) => setRfc(event.target.value)} autoComplete="off" /></label>}<label>Archivo XLSX o CSV<input type="file" accept=".xlsx,.csv" onChange={(event: ChangeEvent<HTMLInputElement>) => setFile(event.target.files?.[0] || null)} /></label><button disabled={busy || !client.can('netpay.inbox.manage') || (datasetType === 'no_usage_campaign' && !rfc)} onClick={() => void upload()}>{busy ? 'Procesando…' : 'Subir y validar'}</button></section>{current && <DatasetDetail batch={current} results={results} busy={busy} onAccept={() => void operate('accept')} onReject={() => void operate('reject')} onResolve={resolve} />}</>}
    {(tab === 'profitability' || tab === 'no_use') && <ResultView title={tab === 'profitability' ? 'Rentabilidad' : 'No uso'} batch={current} results={results} />}
    {tab === 'history' && <History batches={batches} onOpen={open} />}
  </section>;
}

function History({ batches, onOpen }: { batches: OperationalDataBatch[]; onOpen: (batch: OperationalDataBatch) => void }) {
  return <section><h2>Historial de importaciones</h2>{batches.length === 0 ? <p>Sin cargas operativas.</p> : <div className="netpay-table-wrap"><table><thead><tr><th>Tipo</th><th>Periodo</th><th>Estado</th><th>Filas</th><th>Fecha</th></tr></thead><tbody>{batches.map((batch) => <tr key={batch.id}><td><button onClick={() => void onOpen(batch)}>{label(batch.dataset_type)}</button></td><td>{batch.reporting_period || 'No disponible'}</td><td>{label(batch.status)}</td><td>{batch.row_counts.authorized ?? 0}</td><td>{new Intl.DateTimeFormat('es-MX', { dateStyle: 'medium' }).format(new Date(batch.created_at))}</td></tr>)}</tbody></table></div>}</section>;
}

function ResultView({ title, batch, results }: { title: string; batch: OperationalDataBatch | null; results: Record<string, unknown>[] }) {
  if (!batch || batch.status !== 'accepted' || (title === 'Rentabilidad') !== (batch.dataset_type === 'monthly_store_profitability')) return <section><h2>{title}</h2><p>Datos insuficientes. Abre una importación aceptada desde el historial.</p></section>;
  return <section><h2>{title}</h2><p>Periodo {batch.reporting_period || 'No disponible'} · {results.length ? 'Datos disponibles' : 'Registro sin cambio'}</p><Results rows={results} /></section>;
}

function DatasetDetail({ batch, results, busy, onAccept, onReject, onResolve }: { batch: OperationalDataBatch; results: Record<string, unknown>[]; busy: boolean; onAccept: () => void; onReject: () => void; onResolve: (rowId: string, storeReferenceId: string) => void }) {
  const [references, setReferences] = useState<Record<string, string>>({}); const counts = batch.row_counts;
  const keys = ['received','authorized','valid','invalid','matched','unmatched','duplicates','conflicts','projected_inserts','projected_updates','unchanged'];
  const countLabels: Record<string,string> = { received:'Leídas',authorized:'Autorizadas',valid:'Válidas',invalid:'Rechazadas',matched:'Stores encontrados',unmatched:'Stores no encontrados',duplicates:'Duplicados',conflicts:'Conflictos',projected_inserts:'Inserts',projected_updates:'Updates',unchanged:'Sin cambio' };
  return <section className="netpay-detail"><h2>Preview sanitizado</h2><p>{batch.sanitized_filename} · Hoja: {batch.selected_sheet} · Hash: {batch.hash_identifier} · Periodo: {batch.reporting_period || 'No disponible'} · {label(batch.status)}</p><div className="cards">{keys.map((key) => <article className="card" key={key}><small>{countLabels[key]}</small><b>{counts[key] ?? 0}</b></article>)}</div>{batch.status === 'needs_review' && <p><button disabled={busy || counts.invalid > 0 || counts.unmatched > 0 || counts.ambiguous > 0 || counts.conflicts > 0} onClick={onAccept}>Confirmar e importar</button><button disabled={busy} onClick={onReject}>Rechazar batch</button></p>}<div className="netpay-table-wrap"><table><thead><tr><th>Fila</th><th>Store ID</th><th>Periodo</th><th>Vínculo</th><th>Validación</th><th>Proyección</th></tr></thead><tbody>{batch.rows.map((row) => <tr key={row.id}><td>{row.source_row_number}</td><td>{String(row.preview.store_id || 'No disponible')}</td><td>{String(row.preview.reporting_period || 'No disponible')}</td><td>{label(row.match_status)}{row.match_status !== 'matched' && batch.status === 'needs_review' && <span><input aria-label={`Store Reference fila ${row.source_row_number}`} value={references[row.id] || ''} onChange={(event) => setReferences({ ...references, [row.id]: event.target.value })} /><button disabled={busy || !references[row.id]} onClick={() => onResolve(row.id, references[row.id])}>Vincular</button></span>}</td><td>{label(row.validation_status)}{row.error_codes.length ? ` · ${row.error_codes.map((code) => errorLabels[code] || 'Error controlado').join(', ')}` : ''}</td><td>{label(row.projected_action)}</td></tr>)}</tbody></table></div>{batch.status === 'accepted' && <Results rows={results} />}</section>;
}

function Results({ rows }: { rows: Record<string, unknown>[] }) { return <><h3>Resultados normalizados</h3>{rows.length === 0 ? <p>Registro sin cambio.</p> : <div className="netpay-table-wrap"><table><thead><tr><th>Periodo</th><th>Producto/estado</th><th>Volumen/meses sin uso</th><th>Rentabilidad/alerta</th></tr></thead><tbody>{rows.map((row, index) => <tr key={index}><td>{String(row.reporting_period || row.campaign_period || 'No disponible')}</td><td>{String(row.product_uen || row.merchant_status || 'No disponible')}</td><td>{String(row.volume ?? row.months_without_usage ?? 'No disponible')}</td><td>{String(row.profitability ?? row.alert_code ?? 'No disponible')}</td></tr>)}</tbody></table></div>}</> }
