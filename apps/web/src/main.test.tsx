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
      .mockResolvedValueOnce({ ok: true, json: async () => ({ active_cases: 2, open_alerts: 1, critical_alerts: 0, proposed_next_actions: 1, expiring_requirements: 0, recent_events: [] }) })
      .mockResolvedValueOnce({ ok: true, json: async () => [] });

    render(
      <MemoryRouter initialEntries={[('/')]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: /mission control/i })).toBeTruthy();
    expect(await screen.findByText(/active cases/i)).toBeTruthy();
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
});
