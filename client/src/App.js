import { useEffect, useState } from 'react';
import ResourceView from './components/Project.js';
import MyLoginPage from './pages/MyLoginPage.js';
import MyRegistrationPage from './pages/MyRegistrationPage.js';
import { getCurrentSession, signOut } from './api/auth.js';
import { joinProject } from './api/projects.js';
import './App.css';

// Project creation and multi-project selection (US-03/US-05) haven't
// landed -- there is only ever this one seeded project. Every signed-in
// user is joined to it automatically (see handleAuthenticated below,
// US-04) rather than picking from a list that doesn't exist yet.
const PROJECT_ID = 'P1';

export default function App() {
  const [account, setAccount] = useState(null);
  const [authView, setAuthView] = useState('signIn');
  const [joinError, setJoinError] = useState(null);
  // TD-02 -- true only for the brief GET /me round-trip on first mount.
  // Without this, the sign-in form would flash on screen for a moment
  // even when a valid session is about to restore the resource view.
  const [checkingSession, setCheckingSession] = useState(true);

  // TD-02 -- on first mount, ask the server (not localStorage -- the
  // session is a signed, httpOnly cookie the browser already attached to
  // this request) whether we're still signed in from before. A refresh,
  // or even a server restart (the signing key is stable across restarts
  // via server/.env's SECRET_KEY), restores the same signed-in view
  // instead of asking to sign in again.
  useEffect(() => {
    let isCurrent = true;
    getCurrentSession()
      .then((session) => {
        if (isCurrent) setAccount(session);
      })
      .catch(() => {
        // No session (401) or a network hiccup -- either way, nothing to
        // restore. Fall through to the sign-in form below.
      })
      .finally(() => {
        if (isCurrent) setCheckingSession(false);
      });
    return () => {
      isCurrent = false;
    };
  }, []);

  // Runs after both sign-in and sign-up (US-01/US-02 -> US-04). Joining is
  // idempotent server-side -- joining a project you're already in is a
  // no-op, not an error -- so calling it unconditionally here also
  // self-heals any account that existed before this was wired up, not
  // just brand-new sign-ups.
  async function handleAuthenticated(newAccount) {
    setJoinError(null);
    try {
      await joinProject({ projectId: PROJECT_ID, userId: newAccount.userId });
    } catch (error) {
      // Not fatal to signing in -- surfaced so it's not silently
      // swallowed, but ResourceView's own not_a_project_member handling
      // is the real fallback if membership genuinely never took.
      setJoinError(error.message);
    }
    setAccount(newAccount);
  }

  async function handleSignOut() {
    try {
      await signOut();
    } catch (error) {
      // Non-fatal -- clear local state regardless so sign-out never gets
      // stuck on a network error; worst case the old session cookie
      // lingers until it's overwritten by the next sign-in.
    }
    setAccount(null);
    setAuthView('signIn');
  }

  if (checkingSession) {
    return (
      <div className="app-container">
        <p className="muted-text">Checking session...</p>
      </div>
    );
  }

  if (!account) {
    return (
      <div className="app-container">
        {authView === 'signIn' ? (
          <MyLoginPage onSignedIn={handleAuthenticated} onSwitchToSignUp={() => setAuthView('signUp')} />
        ) : (
          <MyRegistrationPage onSignedUp={handleAuthenticated} onSwitchToSignIn={() => setAuthView('signIn')} />
        )}
      </div>
    );
  }

  return (
    <div className="app-container">
      <h1 className="app-heading">Project {PROJECT_ID} — Hardware Resources</h1>
      <p className="app-session">
        <span className="muted-text">Signed in as {account.username}</span>
        <button type="button" className="app-session__sign-out" onClick={handleSignOut}>
          Sign out
        </button>
      </p>
      {joinError && (
        <p role="alert" className="error-text app-session__join-error">
          Couldn't confirm project membership: {joinError}
        </p>
      )}
      <ResourceView projectId={PROJECT_ID} userId={account.userId} />
    </div>
  );
}
