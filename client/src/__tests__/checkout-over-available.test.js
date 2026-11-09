import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Deliberately NOT mocking '../api/hardware.js': this test exercises the real
// checkoutHardware and throwForErrorResponse against a stubbed fetch.
import HardwareSet from '../components/HardwareSet.js';

function jsonResponse(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn());
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('demo step 10: Check Out more than is available', () => {
  it('sends the over-available quantity to the server and shows the insufficient-stock alert', async () => {
    fetch.mockResolvedValue(jsonResponse(409, { error: 'insufficient_stock', onHand: 2, requested: 9 }));
    const onChanged = vi.fn().mockResolvedValue(undefined);
    const hwSet = { hwSetName: 'HWSet1', capacity: 10, available: 2, myCheckedOut: 0, active: true };
    render(<HardwareSet projectId="P1" userId="alice" hwSet={hwSet} onChanged={onChanged} />);

    await userEvent.clear(screen.getByLabelText('Check Out'));
    await userEvent.type(screen.getByLabelText('Check Out'), '9');
    await userEvent.click(screen.getByRole('button', { name: 'Check Out' }));

    expect(await screen.findByRole('alert')).toHaveTextContent("Only 2 available -- can't check out 9.");
    expect(fetch).toHaveBeenCalledTimes(1);
    const [url, options] = fetch.mock.calls[0];
    expect(url).toBe('/api/hardware/checkout');
    expect(options.method).toBe('POST');
    expect(JSON.parse(options.body)).toEqual({
      projectId: 'P1',
      userId: 'alice',
      hwSetName: 'HWSet1',
      quantity: 9,
    });
    expect(onChanged).not.toHaveBeenCalled();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Check Out' })).toBeEnabled());
  });
});
