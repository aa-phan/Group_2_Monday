import { useState } from 'react';
import ResourceView from './components/Project.js';
import MyLoginPage from './pages/MyLoginPage.js';
import MyRegistrationPage from './pages/MyRegistrationPage.js';
import { joinProject } from './api/projects.js';
import './App.css';

// Project creation and multi-project selection (US-03/US-05) haven't
// landed -- there is only ever this one seeded project. Every signed-in
// user is joined to it automatically (see handleAuthenticated below,
// US-04) rather than picking from a list that doesn't exist yet.
const PROJECT_ID = 'P1';

export default function App() {
  // ACCT-04 (session persistence, TD-02) has not landed yet -- this only
  // holds the signed-in identity in memory for the current page load. A
  // refresh signs the user back out; that is expected until TD-02 lands.
  const [account, setAccount] = useState(null);
  const [authView, setAuthView] = useState('signIn');
  const [joinError, setJoinError] = useState(null);

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

  function handleSignOut() {
    setAccount(null);
    setAuthView('signIn');
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
