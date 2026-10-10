import { useState } from 'react';
import ResourceView from './components/Project.js';
import MyLoginPage from './pages/MyLoginPage.js';
import MyRegistrationPage from './pages/MyRegistrationPage.js';
import './App.css';

// Hardware sets live under a project (PROJ-01/02/03, Track A), and that
// create/join flow has not landed yet, so there is no real project to
// source this from. Placeholder for this tracer slice only; Track A
// wires a real projectId in here once project creation/joining lands.
const PROJECT_ID = 'P1';

export default function App() {
  // ACCT-04 (session persistence, TD-02) has not landed yet -- this only
  // holds the signed-in identity in memory for the current page load. A
  // refresh signs the user back out; that is expected until TD-02 lands.
  const [account, setAccount] = useState(null);
  const [authView, setAuthView] = useState('signIn');

  if (!account) {
    return (
      <div className="app-container">
        {authView === 'signIn' ? (
          <MyLoginPage onSignedIn={setAccount} onSwitchToSignUp={() => setAuthView('signUp')} />
        ) : (
          <MyRegistrationPage onSignedUp={setAccount} onSwitchToSignIn={() => setAuthView('signIn')} />
        )}
      </div>
    );
  }

  return (
    <div className="app-container">
      <h1 className="app-heading">Project {PROJECT_ID} — Hardware Resources</h1>
      <p className="muted-text">Signed in as {account.username}</p>
      <ResourceView projectId={PROJECT_ID} userId={account.userId} />
    </div>
  );
}
