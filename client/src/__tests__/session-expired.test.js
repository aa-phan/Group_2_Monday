import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Only auth.js is mocked. The projects page, ResourceView, api/projects.js,
// api/hardware.js and sessionEvents.js are real, so the App tests run the
// whole chain: page -> API module -> sessionEvents -> App.
vi.mock('../api/auth.js', () => ({
  signUp: vi.fn(),
  signIn: vi.fn(),
  getCurrentSession: vi.fn(),
  signOut: vi.fn(),
}));

import { getCurrentSession, signIn, signOut } from '../api/auth.js';
import { checkoutHardware, fetchHardware } from '../api/hardware.js';
import { getUserProjects, joinProject } from '../api/projects.js';
import { notifySignedOut, onSignedOut } from '../api/sessionEvents.js';
import App from '../App.js';

function jsonResponse(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

const NOT_SIGNED_IN = jsonResponse(401, { error: 'not_signed_in' });
const ALICE = { username: 'Alice', userId: 'alice' };
const PROJECTS = jsonResponse(200, {
  projects: [{ projectId: 'P1', projectName: 'Project One', description: '' }],
});

// URL-keyed fetch stub: routes maps a URL prefix to a response.
function stubFetch(routes) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url) => {
      const key = Object.keys(routes).find((prefix) => String(url).startsWith(prefix));
      if (!key) throw new Error(`unexpected fetch ${url}`);
      const value = routes[key];
      return typeof value === 'function' ? value() : value;
    })
  );
}

beforeEach(() => {
  vi.resetAllMocks();
  getCurrentSession.mockResolvedValue(ALICE);
  signOut.mockResolvedValue({});
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('sessionEvents', () => {
  it('calls registered listeners on notify and stops after unsubscribe', () => {
    const listener = vi.fn();
    const unsubscribe = onSignedOut(listener);

    notifySignedOut();
    expect(listener).toHaveBeenCalledTimes(1);

    unsubscribe();
    notifySignedOut();
    expect(listener).toHaveBeenCalledTimes(1);
  });
});

describe('api modules on a 401', () => {
  let listener;
  let unsubscribe;

  beforeEach(() => {
    listener = vi.fn();
    unsubscribe = onSignedOut(listener);
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    unsubscribe();
  });

  it('fetchHardware rejects with not_signed_in and notifies once', async () => {
    fetch.mockResolvedValue(NOT_SIGNED_IN);
    await expect(fetchHardware('P1', 'alice')).rejects.toThrow('not_signed_in');
    expect(listener).toHaveBeenCalledTimes(1);
  });

  it('a POST helper (checkoutHardware) rejects with not_signed_in and notifies once', async () => {
    fetch.mockResolvedValue(NOT_SIGNED_IN);
    await expect(checkoutHardware({ projectId: 'P1', userId: 'alice' })).rejects.toThrow(
      'not_signed_in'
    );
    expect(listener).toHaveBeenCalledTimes(1);
  });

  it('getUserProjects and joinProject reject with not_signed_in and notify', async () => {
    fetch.mockResolvedValue(NOT_SIGNED_IN);
    await expect(getUserProjects({ userId: 'alice' })).rejects.toThrow('not_signed_in');
    await expect(joinProject({ projectId: 'P1', userId: 'alice' })).rejects.toThrow(
      'not_signed_in'
    );
    expect(listener).toHaveBeenCalledTimes(2);
  });

  it.each([
    [403, 'not_a_project_member'],
    [403, 'forbidden_user_mismatch'],
    [409, 'insufficient_stock'],
  ])('a %i %s still rejects but does not notify', async (status, code) => {
    fetch.mockResolvedValue(jsonResponse(status, { error: code }));
    await expect(fetchHardware('P1', 'alice')).rejects.toThrow(code);
    await expect(getUserProjects({ userId: 'alice' })).rejects.toThrow(code);
    expect(listener).not.toHaveBeenCalled();
  });
});

describe('App on a 401 from a data route', () => {
  it('returns to the sign-in view when the project list 401s', async () => {
    stubFetch({ '/get_user_projects_list': NOT_SIGNED_IN });

    render(<App />);

    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    expect(screen.queryByText('Signed in as Alice')).not.toBeInTheDocument();
  });

  it('returns to sign-in when the hardware fetch 401s, and signing in again lands on the picker', async () => {
    stubFetch({
      '/get_user_projects_list': PROJECTS,
      '/api/hardware': NOT_SIGNED_IN,
    });
    const user = userEvent.setup();

    render(<App />);
    await user.click(await screen.findByRole('button', { name: 'Open' }));

    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument();

    signIn.mockResolvedValue(ALICE);
    await user.type(screen.getByLabelText('Username'), 'Alice');
    await user.type(screen.getByLabelText('User ID'), 'alice');
    await user.type(screen.getByLabelText('Password'), 'correct horse battery');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));

    await waitFor(() => expect(screen.getByText('Signed in as Alice')).toBeInTheDocument());
    expect(await screen.findByRole('button', { name: 'Open' })).toBeInTheDocument();
    expect(screen.queryByText(/Hardware Resources/)).not.toBeInTheDocument();
  });
});
