import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

const fetchMock = vi.fn();

global.fetch = fetchMock as unknown as typeof fetch;

describe('Yarvis web app', () => {
  beforeEach(() => {
    fetchMock.mockReset();
  });

  it('renders mission control with real API data', async () => {
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => ({ pending_reports: 2, critical_stores: 1, churn_candidates: 3, assets_without_store: 0, identity_conflicts: 0 }) });

    render(
      <MemoryRouter initialEntries={[('/')]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: /mission control/i })).toBeTruthy();
    expect(await screen.findByText(/pending reports/i)).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Netpay Inbox' }).getAttribute('href')).toBe('/netpay-inbox');
  });

  it('allows sending a message and confirming context', async () => {
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 'conversation-1' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ message: { id: 'message-1', role: 'user', text_content: 'Hola' }, intake_item_id: 'intake-1', system_message: 'Listo' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'confirmed', evidence_id: 'evidence-1' }) });

    render(
      <MemoryRouter initialEntries={[('/conversation')]}>
        <App />
      </MemoryRouter>,
    );

    const user = userEvent.setup();
    await user.type(screen.getByPlaceholderText(/escribe un mensaje/i), 'Hola');
    await user.click(screen.getByRole('button', { name: /enviar/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(await screen.findByText(/Listo/i)).toBeTruthy();
  });

  it('shows an API error state', async () => {
    fetchMock.mockRejectedValueOnce(new Error('boom'));

    render(
      <MemoryRouter initialEntries={[('/')]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/No se pudo conectar con la API/i)).toBeTruthy();
  });

  it('redirects the legacy NetPay XLSX route to Datos Netpay', async () => {
    render(
      <MemoryRouter initialEntries={['/netpay-intake']}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: /datos netpay/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /importar xlsx/i })).toBeTruthy();
  });

  it('renders the recovery queue empty state without deriving actions', async () => {
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => ({ profiles: [], pending_profiles: 0 }) }).mockResolvedValueOnce({ ok: true, json: async () => ({ pending_profiles: 0, historical_only_profiles: 2, incomplete_profiles: 1 }) });
    render(<MemoryRouter initialEntries={['/recovery-queue']}><App /></MemoryRouter>);
    expect(await screen.findByRole('heading', { name: /cola de recuperación/i })).toBeTruthy();
    expect(await screen.findByText(/Ningún comercio califica actualmente/i)).toBeTruthy();
  });
});
