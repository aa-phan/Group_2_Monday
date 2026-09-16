import InventoryView from './components/Project.js';
import './App.css';

// Track A's session/auth layer (ACCT-04) has not landed yet, so there is no
// login flow to source householdId/userId from. These are placeholder
// identifiers for this tracer slice only; the seeded household for local
// development is documented in the phase SUMMARY. Track A wires real
// session values in here once ACCT-04 lands.
const HOUSEHOLD_ID = 'H1';
const USER_ID = 'alice';

export default function App() {
  return (
    <div className="app-container">
      <h1 className="app-heading">{HOUSEHOLD_ID} Pantry</h1>
      <InventoryView householdId={HOUSEHOLD_ID} userId={USER_ID} />
    </div>
  );
}
