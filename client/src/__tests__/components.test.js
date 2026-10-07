import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createEvent, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../api/hardware.js', () => ({
  fetchHardware: vi.fn(),
  checkinHardware: vi.fn(),
  checkoutHardware: vi.fn(),
}));

import { checkinHardware, checkoutHardware, fetchHardware } from '../api/hardware.js';
import Availability from '../components/Availability.js';
import Capacity from '../components/Capacity.js';
import CheckIn from '../components/CheckIn.js';
import CheckOut from '../components/CheckOut.js';
import HardwareSet from '../components/HardwareSet.js';
import QuantityAction from '../components/QuantityAction.js';
import ResourceView from '../components/Project.js';

beforeEach(() => {
  vi.resetAllMocks();
});

describe('Availability and Capacity', () => {
  it('Availability shows its label and value, including zero', () => {
    render(<Availability available={0} />);
    expect(screen.getByText('Available')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('Capacity shows its label and value', () => {
    render(<Capacity capacity={12} />);
    expect(screen.getByText('Capacity')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
  });
});

describe('QuantityAction', () => {
  function setup(overrides = {}) {
    const props = {
      label: 'Do It',
      busyLabel: 'Doing...',
      action: vi.fn().mockResolvedValue(undefined),
      describeError: (error) => `described: ${error.message}`,
      onChanged: vi.fn().mockResolvedValue(undefined),
      ...overrides,
    };
    render(<QuantityAction {...props} />);
    return props;
  }

  it('starts at quantity 1 and submits the numeric quantity then reloads', async () => {
    const props = setup();
    const input = screen.getByLabelText('Do It');
    expect(input).toHaveValue(1);

    await userEvent.clear(input);
    await userEvent.type(input, '4');
    await userEvent.click(screen.getByRole('button', { name: 'Do It' }));

    expect(props.action).toHaveBeenCalledWith(4);
    expect(typeof props.action.mock.calls[0][0]).toBe('number');
    await waitFor(() => expect(props.onChanged).toHaveBeenCalledTimes(1));
  });

  it('disables the button and shows the busy label while the action is in flight', async () => {
    let finish;
    const action = vi.fn(() => new Promise((resolve) => { finish = resolve; }));
    setup({ action });

    await userEvent.click(screen.getByRole('button', { name: 'Do It' }));

    const busyButton = await screen.findByRole('button', { name: 'Doing...' });
    expect(busyButton).toBeDisabled();

    finish();
    const idleButton = await screen.findByRole('button', { name: 'Do It' });
    expect(idleButton).toBeEnabled();
  });

  it('shows the described error as an alert and does not reload when the action fails', async () => {
    const props = setup({ action: vi.fn().mockRejectedValue(new Error('boom')) });

    await userEvent.click(screen.getByRole('button', { name: 'Do It' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('described: boom');
    expect(props.onChanged).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Do It' })).toBeEnabled();
  });

  it('clears a previous error when the next attempt succeeds', async () => {
    const action = vi
      .fn()
      .mockRejectedValueOnce(new Error('boom'))
      .mockResolvedValueOnce(undefined);
    setup({ action });

    await userEvent.click(screen.getByRole('button', { name: 'Do It' }));
    expect(await screen.findByRole('alert')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Do It' }));
    await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument());
  });

  it('declares a whole-number input with a minimum of 1', () => {
    setup();
    const input = screen.getByLabelText('Do It');
    expect(input).toHaveAttribute('type', 'number');
    expect(input).toHaveAttribute('min', '1');
    expect(input).toHaveAttribute('step', '1');
  });

  it('prevents the browser from submitting the form natively', () => {
    setup();
    const form = screen.getByRole('button', { name: 'Do It' }).closest('form');
    const event = createEvent.submit(form);
    fireEvent(form, event);
    expect(event.defaultPrevented).toBe(true);
  });

  it('keeps the entered quantity after a successful action', async () => {
    setup();
    const input = screen.getByLabelText('Do It');
    await userEvent.clear(input);
    await userEvent.type(input, '7');
    await userEvent.click(screen.getByRole('button', { name: 'Do It' }));

    await waitFor(() => expect(input).toHaveValue(7));
  });
});

describe('CheckOut', () => {
  const props = { projectId: 'P1', userId: 'alice', hwSetName: 'HWSet1' };

  it('calls checkoutHardware with the full payload and reloads', async () => {
    checkoutHardware.mockResolvedValue({});
    const onChanged = vi.fn().mockResolvedValue(undefined);
    render(<CheckOut {...props} onChanged={onChanged} />);

    await userEvent.clear(screen.getByLabelText('Check Out'));
    await userEvent.type(screen.getByLabelText('Check Out'), '3');
    await userEvent.click(screen.getByRole('button', { name: 'Check Out' }));

    expect(checkoutHardware).toHaveBeenCalledWith({
      projectId: 'P1',
      userId: 'alice',
      hwSetName: 'HWSet1',
      quantity: 3,
    });
    await waitFor(() => expect(onChanged).toHaveBeenCalled());
  });

  it('says how many are available when checking out too many', async () => {
    checkoutHardware.mockRejectedValue(Object.assign(new Error('insufficient_stock'), { onHand: 2, requested: 9 }));
    render(<CheckOut {...props} onChanged={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: 'Check Out' }));

    expect(await screen.findByRole('alert')).toHaveTextContent("Only 2 available -- can't check out 9.");
  });

  it('reports zero available rather than falling through to the raw error code', async () => {
    checkoutHardware.mockRejectedValue(Object.assign(new Error('insufficient_stock'), { onHand: 0, requested: 1 }));
    render(<CheckOut {...props} onChanged={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: 'Check Out' }));

    expect(await screen.findByRole('alert')).toHaveTextContent("Only 0 available -- can't check out 1.");
  });

  it('asks for a whole number when the server rejects the quantity', async () => {
    checkoutHardware.mockRejectedValue(Object.assign(new Error('invalid_input'), { field: 'quantity' }));
    render(<CheckOut {...props} onChanged={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: 'Check Out' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Enter a whole number of 1 or more.');
  });

  it('shows the raw message for any other error', async () => {
    checkoutHardware.mockRejectedValue(new Error('not_a_project_member'));
    render(<CheckOut {...props} onChanged={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: 'Check Out' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('not_a_project_member');
  });
});

describe('CheckIn', () => {
  const props = { projectId: 'P1', userId: 'alice', hwSetName: 'HWSet1' };

  it('calls checkinHardware with the full payload and reloads', async () => {
    checkinHardware.mockResolvedValue({});
    const onChanged = vi.fn().mockResolvedValue(undefined);
    render(<CheckIn {...props} onChanged={onChanged} />);

    await userEvent.clear(screen.getByLabelText('Check In'));
    await userEvent.type(screen.getByLabelText('Check In'), '2');
    await userEvent.click(screen.getByRole('button', { name: 'Check In' }));

    expect(checkinHardware).toHaveBeenCalledWith({
      projectId: 'P1',
      userId: 'alice',
      hwSetName: 'HWSet1',
      quantity: 2,
    });
    await waitFor(() => expect(onChanged).toHaveBeenCalled());
  });

  it('says how many are checked out when checking in too many', async () => {
    checkinHardware.mockRejectedValue(
      Object.assign(new Error('checkin_exceeds_checked_out'), { checkedOut: 2, requested: 5 })
    );
    render(<CheckIn {...props} onChanged={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: 'Check In' }));

    expect(await screen.findByRole('alert')).toHaveTextContent("Only 2 checked out -- can't check in 5.");
  });

  it('reports zero checked out rather than the raw error code', async () => {
    checkinHardware.mockRejectedValue(
      Object.assign(new Error('checkin_exceeds_checked_out'), { checkedOut: 0, requested: 1 })
    );
    render(<CheckIn {...props} onChanged={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: 'Check In' }));

    expect(await screen.findByRole('alert')).toHaveTextContent("Only 0 checked out -- can't check in 1.");
  });

  it('asks for a whole number when the server rejects the quantity', async () => {
    checkinHardware.mockRejectedValue(Object.assign(new Error('invalid_input'), { field: 'quantity' }));
    render(<CheckIn {...props} onChanged={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: 'Check In' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Enter a whole number of 1 or more.');
  });

  it('shows the raw message for any other error', async () => {
    checkinHardware.mockRejectedValue(new Error('hardware_set_not_found'));
    render(<CheckIn {...props} onChanged={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: 'Check In' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('hardware_set_not_found');
  });
});

describe('HardwareSet', () => {
  it('shows the set name and its four components in order', () => {
    const hwSet = { hwSetName: 'HWSet1', capacity: 10, available: 6 };
    render(<HardwareSet projectId="P1" userId="alice" hwSet={hwSet} onChanged={vi.fn()} />);

    const region = screen.getByRole('region', { name: 'HWSet1' });
    expect(screen.getByRole('heading', { name: 'HWSet1' })).toBeInTheDocument();
    const labels = Array.from(region.querySelectorAll('.hw-cell__label')).map((node) =>
      node.textContent.replace(/\d+$/, '').trim()
    );
    expect(labels).toEqual(['Available', 'Capacity', 'Check In', 'Check Out']);
    expect(region).toHaveTextContent('6');
    expect(region).toHaveTextContent('10');
  });

  it('wires both actions to this set, project, and user', async () => {
    checkinHardware.mockResolvedValue({});
    checkoutHardware.mockResolvedValue({});
    const hwSet = { hwSetName: 'HWSet2', capacity: 5, available: 5 };
    render(<HardwareSet projectId="P9" userId="bob" hwSet={hwSet} onChanged={vi.fn().mockResolvedValue()} />);

    await userEvent.click(screen.getByRole('button', { name: 'Check In' }));
    await userEvent.click(screen.getByRole('button', { name: 'Check Out' }));

    const expected = { projectId: 'P9', userId: 'bob', hwSetName: 'HWSet2', quantity: 1 };
    expect(checkinHardware).toHaveBeenCalledWith(expected);
    expect(checkoutHardware).toHaveBeenCalledWith(expected);
  });
});

describe('ResourceView', () => {
  const sets = [
    { hwSetName: 'HWSet1', capacity: 10, available: 10 },
    { hwSetName: 'HWSet2', capacity: 20, available: 15 },
  ];

  it('shows a loading message, then one card per set in the order received', async () => {
    fetchHardware.mockResolvedValue({ hardwareSets: sets });
    render(<ResourceView projectId="P1" userId="alice" />);

    expect(screen.getByText('Loading hardware resources...')).toBeInTheDocument();
    const regions = await screen.findAllByRole('region');
    expect(regions.map((region) => region.getAttribute('aria-label'))).toEqual(['HWSet1', 'HWSet2']);
    expect(fetchHardware).toHaveBeenCalledWith('P1', 'alice');
  });

  it('says so when the project has no hardware sets', async () => {
    fetchHardware.mockResolvedValue({ hardwareSets: [] });
    render(<ResourceView projectId="P1" userId="alice" />);

    expect(await screen.findByText('No hardware sets in this project yet.')).toBeInTheDocument();
  });

  it('treats a response without hardwareSets as empty', async () => {
    fetchHardware.mockResolvedValue(null);
    render(<ResourceView projectId="P1" userId="alice" />);

    expect(await screen.findByText('No hardware sets in this project yet.')).toBeInTheDocument();
  });

  it('shows the error with a Retry button that refetches', async () => {
    fetchHardware
      .mockRejectedValueOnce(new Error('not_a_project_member'))
      .mockResolvedValueOnce({ hardwareSets: sets });
    render(<ResourceView projectId="P1" userId="alice" />);

    expect(await screen.findByText('not_a_project_member')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }));

    expect(await screen.findByRole('region', { name: 'HWSet1' })).toBeInTheDocument();
    expect(fetchHardware).toHaveBeenCalledTimes(2);
  });

  it('refreshes the numbers after a checkout without unmounting the cards', async () => {
    fetchHardware
      .mockResolvedValueOnce({ hardwareSets: [{ hwSetName: 'HWSet1', capacity: 10, available: 10 }] })
      .mockResolvedValueOnce({ hardwareSets: [{ hwSetName: 'HWSet1', capacity: 10, available: 7 }] });
    checkoutHardware.mockResolvedValue({});
    render(<ResourceView projectId="P1" userId="alice" />);

    const region = await screen.findByRole('region', { name: 'HWSet1' });
    await userEvent.clear(screen.getByLabelText('Check Out'));
    await userEvent.type(screen.getByLabelText('Check Out'), '3');
    await userEvent.click(screen.getByRole('button', { name: 'Check Out' }));

    await waitFor(() => expect(region).toHaveTextContent('7'));
    expect(screen.queryByText('Loading hardware resources...')).not.toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'HWSet1' })).toBe(region);
  });

  it('refetches when the project or user changes', async () => {
    fetchHardware.mockResolvedValue({ hardwareSets: sets });
    const { rerender } = render(<ResourceView projectId="P1" userId="alice" />);
    await screen.findAllByRole('region');

    rerender(<ResourceView projectId="P2" userId="alice" />);
    await waitFor(() => expect(fetchHardware).toHaveBeenCalledWith('P2', 'alice'));

    rerender(<ResourceView projectId="P2" userId="bob" />);
    await waitFor(() => expect(fetchHardware).toHaveBeenCalledWith('P2', 'bob'));
  });
});
