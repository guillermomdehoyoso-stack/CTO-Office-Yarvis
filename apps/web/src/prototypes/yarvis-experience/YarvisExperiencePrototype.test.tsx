import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { YarvisExperiencePrototype } from './YarvisExperiencePrototype';

describe('YarvisExperiencePrototype', () => {
  it('renders all configured Spaces and supports structured fallback and scenario switching', async () => {
    const user = userEvent.setup(); render(<YarvisExperiencePrototype />);
    expect(screen.getByRole('button', { name: /Energía Fotónica/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /NetPay/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Trading \/ Finance/i })).toBeTruthy();
    await user.click(screen.getByRole('button', { name: /Show structured fallback/i }));
    expect(screen.getByRole('button', { name: /Show spatial field/i })).toBeTruthy();
    await user.selectOptions(screen.getByLabelText('Scenario'), 'energy_attention');
    expect(screen.getByText(/Energía Fotónica needs attention/i)).toBeTruthy();
  });

  it('supports keyboard navigation through Space, Area, Workspace and Back', async () => {
    const user = userEvent.setup(); render(<YarvisExperiencePrototype />);
    const energy = screen.getByRole('button', { name: /Energía Fotónica/i }); energy.focus(); await user.keyboard('{Enter}');
    expect(screen.getByRole('heading', { name: 'Energía Fotónica' })).toBeTruthy();
    await user.click(screen.getByRole('button', { name: /Engineering/i }));
    expect(screen.getByRole('heading', { name: 'Engineering' })).toBeTruthy();
    await user.click(screen.getByRole('button', { name: /Open structured workspace preview/i }));
    expect(screen.getByRole('heading', { name: /Operational workspace preview/i })).toBeTruthy();
    await user.keyboard('{Escape}');
    expect(screen.getByRole('heading', { name: 'Engineering' })).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByRole('heading', { name: 'Engineering' }));
    await user.keyboard('{Escape}');
    expect(screen.getByRole('heading', { name: 'Energía Fotónica' })).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByRole('heading', { name: 'Energía Fotónica' }));
    await user.keyboard('{Escape}');
    expect(screen.getByText(/Your operational universe/i)).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByRole('heading', { name: /Your operational universe/i }));
  });

  it('provides a reduced-motion control without losing labels or navigation', async () => {
    const user = userEvent.setup(); render(<YarvisExperiencePrototype />);
    await user.click(screen.getByRole('button', { name: 'Reduce motion' }));
    expect(screen.getByRole('button', { name: 'Enable motion' })).toBeTruthy();
    expect(screen.getByRole('button', { name: /NetPay/i }).getAttribute('aria-label')).toContain('active work items');
  });
});
