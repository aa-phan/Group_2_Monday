import { beforeEach, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../api/auth.js', () => ({
  signUp: vi.fn(),
  signIn: vi.fn(),
}));

// Project.js/ResourceView fetches real hardware data via api/hardware.js --
// irrelevant to what App.js itself is responsible for (showing auth vs.
// the resource view, and handing it the right userId). Stubbed so these
// tests only exercise App's own wiring.
vi.mock('../components/Project.js', () => ({
  default: ({ projectId, userId }) => (
    <div data-testid="resource-view">{projectId}:{userId}</div>
  ),
}));

import { signIn, signUp } from '../api/auth.js';
import App from '../App.js';

beforeEach(() => {
  vi.resetAllMocks();
});

it('shows the sign-in form by default, before any account is set', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
});

it('switches to the sign-up form and back without signing in', async () => {
  render(<App />);

  await userEvent.click(screen.getByRole('button', { name: 'Sign up' }));
  expect(screen.getByRole('heading', { name: 'Create an account' })).toBeInTheDocument();

  await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));
  expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
});

it('renders the resource view with the signed-in userId after a successful sign-in', async () => {
  signIn.mockResolvedValue({ username: 'alice', userId: 'alice1' });
  render(<App />);

  await userEvent.type(screen.getByLabelText('Username'), 'alice');
  await userEvent.type(screen.getByLabelText('User ID'), 'alice1');
  await userEvent.type(screen.getByLabelText('Password'), 'correct horse battery');
  await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));

  expect(await screen.findByTestId('resource-view')).toHaveTextContent('P1:alice1');
  expect(screen.getByText('Signed in as alice')).toBeInTheDocument();
});

it('renders the resource view with the created userId after a successful sign-up', async () => {
  signUp.mockResolvedValue({ username: 'bob', userId: 'bob1' });
  render(<App />);

  await userEvent.click(screen.getByRole('button', { name: 'Sign up' }));
  await userEvent.type(screen.getByLabelText('Username'), 'bob');
  await userEvent.type(screen.getByLabelText('User ID'), 'bob1');
  await userEvent.type(screen.getByLabelText('Password'), 'correct horse battery');
  await userEvent.type(screen.getByLabelText('Confirm password'), 'correct horse battery');
  await userEvent.click(screen.getByRole('button', { name: 'Create account' }));

  expect(await screen.findByTestId('resource-view')).toHaveTextContent('P1:bob1');
});
