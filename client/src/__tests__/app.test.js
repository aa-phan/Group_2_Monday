import { beforeEach, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../api/auth.js', () => ({
  signUp: vi.fn(),
  signIn: vi.fn(),
}));

vi.mock('../api/projects.js', () => ({
  joinProject: vi.fn(),
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
import { joinProject } from '../api/projects.js';
import App from '../App.js';

beforeEach(() => {
  vi.resetAllMocks();
  // Every existing test signs in/up without caring about the join step --
  // default it to success so those tests aren't newly on the hook for it.
  joinProject.mockResolvedValue({ userId: 'irrelevant', projectId: 'P1' });
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

it('returns to the sign-in form after signing out, clearing the session', async () => {
  signIn.mockResolvedValue({ username: 'alice', userId: 'alice1' });
  render(<App />);

  await userEvent.type(screen.getByLabelText('Username'), 'alice');
  await userEvent.type(screen.getByLabelText('User ID'), 'alice1');
  await userEvent.type(screen.getByLabelText('Password'), 'correct horse battery');
  await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));
  await screen.findByTestId('resource-view');

  await userEvent.click(screen.getByRole('button', { name: 'Sign out' }));

  expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
  expect(screen.queryByTestId('resource-view')).not.toBeInTheDocument();
  expect(screen.queryByText('Signed in as alice')).not.toBeInTheDocument();
});

it('signing back in after a sign-out starts a fresh username/password field', async () => {
  signIn.mockResolvedValue({ username: 'alice', userId: 'alice1' });
  render(<App />);

  await userEvent.type(screen.getByLabelText('Username'), 'alice');
  await userEvent.type(screen.getByLabelText('User ID'), 'alice1');
  await userEvent.type(screen.getByLabelText('Password'), 'correct horse battery');
  await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));
  await screen.findByTestId('resource-view');
  await userEvent.click(screen.getByRole('button', { name: 'Sign out' }));

  expect(screen.getByLabelText('Username')).toHaveValue('');
});

it('joins the signed-in user to project P1 (US-04) before showing the resource view', async () => {
  signIn.mockResolvedValue({ username: 'alice', userId: 'alice1' });
  render(<App />);

  await userEvent.type(screen.getByLabelText('Username'), 'alice');
  await userEvent.type(screen.getByLabelText('User ID'), 'alice1');
  await userEvent.type(screen.getByLabelText('Password'), 'correct horse battery');
  await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));

  await screen.findByTestId('resource-view');
  expect(joinProject).toHaveBeenCalledWith({ projectId: 'P1', userId: 'alice1' });
});

it('also joins a brand-new sign-up to project P1, not just sign-ins', async () => {
  signUp.mockResolvedValue({ username: 'bob', userId: 'bob1' });
  render(<App />);

  await userEvent.click(screen.getByRole('button', { name: 'Sign up' }));
  await userEvent.type(screen.getByLabelText('Username'), 'bob');
  await userEvent.type(screen.getByLabelText('User ID'), 'bob1');
  await userEvent.type(screen.getByLabelText('Password'), 'correct horse battery');
  await userEvent.type(screen.getByLabelText('Confirm password'), 'correct horse battery');
  await userEvent.click(screen.getByRole('button', { name: 'Create account' }));

  await screen.findByTestId('resource-view');
  expect(joinProject).toHaveBeenCalledWith({ projectId: 'P1', userId: 'bob1' });
});

it('still signs the user in and shows a message when joining fails', async () => {
  signIn.mockResolvedValue({ username: 'alice', userId: 'alice1' });
  joinProject.mockRejectedValue(new Error('project_not_found'));
  render(<App />);

  await userEvent.type(screen.getByLabelText('Username'), 'alice');
  await userEvent.type(screen.getByLabelText('User ID'), 'alice1');
  await userEvent.type(screen.getByLabelText('Password'), 'correct horse battery');
  await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));

  // Not fatal -- still reaches the resource view (whose own
  // not_a_project_member handling is the real fallback).
  expect(await screen.findByTestId('resource-view')).toBeInTheDocument();
  expect(await screen.findByRole('alert')).toHaveTextContent('project_not_found');
});
