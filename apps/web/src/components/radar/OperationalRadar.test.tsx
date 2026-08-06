import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { OperationalRadar } from './OperationalRadar';

afterEach(() => vi.restoreAllMocks());

describe('OperationalRadar', () => {
  it('renders the actionable dashboard with pending merchants', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ summary: { pending: 3, overdue: 1, tpv: 2, ecommerce: 2 }, merchants: [{ id: 'merchant-1', trade_name: 'Gasolinera La Providencia', products: ['ecommerce'], pending: true, open_count: 1, next_action: 'Solicitar INE', due_at: null, priority: 'high', missing_documents: ['INE'], owner: 'Guillermo' }] }) }));
    render(<OperationalRadar />);
    expect(await screen.findByText('Radar Operativo Netpay')).toBeTruthy();
    expect(await screen.findByText('Gasolinera La Providencia')).toBeTruthy();
    expect(screen.getByText('PENDIENTE ON')).toBeTruthy();
  });

  it('keeps the close dialog open and exposes an API rejection', async () => {
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/radar/dashboard')) return Promise.resolve({ ok: true, json: async () => ({ summary: {}, merchants: [{ id: 'merchant-1', trade_name: 'Comercio', products: ['tpv'], pending: true, open_count: 1, missing_documents: [] }] }) });
      if (url.includes('/radar/merchants/merchant-1')) return Promise.resolve({ ok: true, json: async () => ({ id: 'merchant-1', trade_name: 'Comercio', products: ['tpv'], pending: true, open_count: 1, missing_documents: [], requests: [{ id: 'request-1', merchant_id: 'merchant-1', classification: 'soporte', status: 'open', free_text: 'Caso', next_action: 'Llamar', owner: 'Ana', checklist: [] }], activity: [] }) });
      return Promise.resolve({ ok: false, text: async () => 'next action and required checklist must be resolved or justified' });
    }));
    const user = userEvent.setup();
    render(<OperationalRadar />);
    await user.click(await screen.findByText('Comercio', { selector: 'b' }));
    await user.click(await screen.findByRole('button', { name: 'Cerrar solicitud' }));
    await user.click(screen.getByRole('button', { name: 'Aceptar y cerrar' }));
    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByRole('dialog')).toBeTruthy();
  });
});
