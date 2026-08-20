import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { NetpayApiClient } from '../../api/netpay';
import { NetpayDataWorkspace } from './NetpayDataWorkspace';

const batch = { id: 'batch-1', dataset_type: 'monthly_store_profitability', reporting_period: '2026-08', sanitized_filename: 'synthetic.csv', selected_sheet: 'CSV', hash_identifier: 'abc123', preview_token: 'a'.repeat(64), duplicate_upload: false, status: 'needs_review', row_counts: { received: 1, authorized: 1, valid: 1, invalid: 0, matched: 1, unmatched: 0, ambiguous: 0, conflicts: 0, duplicates: 0, projected_inserts: 1, projected_updates: 0, unchanged: 0 }, source_discarded: true, created_at: '2026-08-19T00:00:00Z', updated_at: '2026-08-19T00:00:00Z', rows: [{ id: 'row-1', source_row_number: 2, validation_status: 'valid', match_status: 'matched', store_reference_id: 'store-1', error_codes: [], projected_action: 'insert', preview: { store_id: '***0001', reporting_period: '2026-08' } }] };
function configured() { const client = new NetpayApiClient({ baseUrl: 'http://api.test', subject: 'operator:test', organizationSelector: 'org-test', organizationLabel: 'Organización sintética', authToken: 'token', capabilities: new Set(['netpay.inbox.read', 'netpay.inbox.manage']) }); vi.spyOn(client, 'listOperationalDatasets').mockResolvedValue({ items: [], total: 0 }); vi.spyOn(client, 'uploadOperationalDataset').mockResolvedValue(batch); vi.spyOn(client, 'acceptOperationalDataset').mockResolvedValue({ ...batch, status: 'accepted' }); vi.spyOn(client, 'getOperationalDatasetResults').mockResolvedValue([{ reporting_period: '2026-08', product_uen: 'TPV', volume: 1, profitability: 2 }]); return client; }

it('uploads a synthetic dataset, displays sanitized preview, accepts it and refreshes history', async () => {
  const client = configured(); render(<NetpayDataWorkspace client={client} />); await waitFor(() => expect(client.listOperationalDatasets).toHaveBeenCalled());
  const input = screen.getByLabelText(/Archivo XLSX/i); const file = new File(['Store ID,Client ID,Mes,Rentabilidad\nSYN-1,C-1,2026-08,1'], 'synthetic.csv', { type: 'text/csv' }); await userEvent.upload(input, file); await userEvent.click(screen.getByRole('button', { name: /Subir y validar/i }));
  expect(await screen.findByText(/Preview sanitizado/i)).toBeTruthy(); expect(screen.getByText('***0001')).toBeTruthy(); await userEvent.click(screen.getByRole('button', { name: /Confirmar e importar/i })); await waitFor(() => expect(client.getOperationalDatasetResults).toHaveBeenCalledWith('batch-1'));
});

it('requires the ephemeral RFC value only for no-usage uploads', async () => {
  const client = configured(); render(<NetpayDataWorkspace client={client} />); await waitFor(() => expect(client.listOperationalDatasets).toHaveBeenCalled()); await userEvent.selectOptions(screen.getByLabelText(/Tipo de dataset/i), 'no_usage_campaign'); expect(screen.getByLabelText(/RFC de distribuidor/i)).toBeTruthy(); expect((screen.getByRole('button', { name: /Subir y validar/i }) as HTMLButtonElement).disabled).toBe(true);
});
