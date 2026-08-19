import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { OperationalRadar } from './OperationalRadar';

function LocationProbe() {
  return <p>{useLocation().pathname}</p>;
}

describe('OperationalRadar', () => {
  it('redirects the retired Radar entry point to the canonical Netpay Inbox', () => {
    render(
      <MemoryRouter initialEntries={['/radar-netpay']}>
        <Routes>
          <Route path="/radar-netpay" element={<OperationalRadar />} />
          <Route path="/netpay-inbox" element={<LocationProbe />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('/netpay-inbox')).toBeTruthy();
  });
});
