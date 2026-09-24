import { useCallback, useEffect, useState } from 'react';
import { fetchInventory } from '../api/inventory.js';
import BatchList from './BatchList.js';
import FreshnessBadge from './FreshnessBadge.js';
import ItemActions from './Checkout.js';
import RestockForm from './RestockForm.js';

const LOCATION_ORDER = ['Pantry', 'Fridge', 'Freezer'];

/**
 * AmbiguityNotice renders the message shown when a restock could not be
 * merged into an existing item because more than one existing item could
 * match it.
 *
 * Data source: props only
 * No hard-coded fallback: this component renders nothing it was not given or told.
 *
 * @component
 * @param {Object} props
 * @param {Object} props.notice - Carries `itemName`, `itemKey`, `location`,
 *   and `candidates` describing the restock that could not be merged.
 */
function AmbiguityNotice({ notice }) {
  return (
    <p className="ambiguity-notice">
      &quot;{notice.itemName}&quot; wasn&apos;t merged into an existing item because it could
      match more than one: {notice.candidates.join(', ')}. A separate item was created instead.
    </p>
  );
}

/**
 * LocationSection renders one storage location's (Pantry, Fridge, or
 * Freezer) list of item cards.
 *
 * Data source: props only
 * No hard-coded fallback: this component renders nothing it was not given or told.
 *
 * @component
 * @param {Object} props
 * @param {string} props.location - One of Pantry, Fridge, or Freezer. Also
 *   selects the item card's location-stripe modifier class.
 * @param {Array} props.items - The already-fetched item array for this
 *   location, rendered in the order received.
 * @param {Object} [props.ambiguityNotice] - Nullable; the ambiguity notice
 *   to show alongside the matching item, if any.
 * @param {string} props.userId - Pass-through session identity; never read
 *   or defaulted here, only forwarded to `ItemActions`.
 * @param {string} props.userName - Pass-through session identity; never
 *   read or defaulted here, only forwarded to `ItemActions`.
 * @param {Function} props.onChanged - The reload callback forwarded to
 *   `ItemActions`.
 */
function LocationSection({ location, items, ambiguityNotice, userId, userName, onChanged }) {
  return (
    <section className="location-section">
      <h2>{location}</h2>
      {items.length === 0 ? (
        <p className="muted-text">Nothing stored here yet.</p>
      ) : (
        <ul className="item-card-list">
          {items.map((item) => (
            <li key={item.itemKey} className={`item-card item-card--${location.toLowerCase()}`}>
              <details className="item-disclosure">
                <summary className="item-summary">
                  <span className="item-summary__name">{item.itemName}</span>
                  <span className="item-summary__capacity">Capacity: {item.capacity}</span>
                  <span className="item-summary__availability">
                    Available: {item.availability}
                  </span>
                  <FreshnessBadge freshness={item.freshness} location={location} />
                </summary>
                <BatchList batches={item.batches} location={location} />
                {ambiguityNotice && ambiguityNotice.itemKey === item.itemKey && (
                  <AmbiguityNotice notice={ambiguityNotice} />
                )}
                <ItemActions
                  item={item}
                  userId={userId}
                  userName={userName}
                  onChanged={onChanged}
                />
              </details>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/**
 * InventoryView is the top-level presentational component for a household's
 * inventory. It fetches its own inventory data through
 * client/src/api/inventory.js, but accepts session identity as props rather
 * than reading it from any global auth state -- Track A's session/auth layer
 * wires real values in here once it lands.
 *
 * See .planning/phases/05-ui-design/05-DESIGN.md for the full contract.
 *
 * Data source: fetches via client/src/api/inventory.js
 * No hard-coded fallback: this component renders nothing it was not given or told.
 *
 * @component
 * @param {Object} props
 * @param {string} props.householdId - The household whose inventory to load.
 *   No fallback/default; a real session must supply this.
 * @param {string} props.userId - The acting user's id, used for reserve/
 *   consume/release calls. No fallback/default.
 * @param {string} props.userName - Display name shown on reservation entries
 *   this user creates. No fallback/default.
 */
export default function InventoryView({ householdId, userId, userName }) {
  const [inventory, setInventory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [ambiguityNotice, setAmbiguityNotice] = useState(null);

  const loadInventory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchInventory(householdId, userId);
      setInventory(data);
    } catch (fetchError) {
      setError(fetchError.message);
    } finally {
      setLoading(false);
    }
  }, [householdId, userId]);

  useEffect(() => {
    loadInventory();
  }, [loadInventory]);

  const handleRestocked = useCallback(
    async (restockedItem) => {
      setAmbiguityNotice(
        restockedItem && restockedItem.matchAmbiguity
          ? {
              location: restockedItem.location,
              itemKey: restockedItem.itemKey,
              itemName: restockedItem.itemName,
              candidates: restockedItem.matchAmbiguity,
            }
          : null
      );
      await loadInventory();
    },
    [loadInventory]
  );

  if (loading) {
    return <p>Loading inventory...</p>;
  }

  if (error) {
    return (
      <div>
        <p className="error-text">{error}</p>
        <button type="button" onClick={loadInventory}>
          Retry
        </button>
      </div>
    );
  }

  const locations = inventory ? inventory.locations : {};

  return (
    <div>
      {LOCATION_ORDER.map((location) => (
        <LocationSection
          key={location}
          location={location}
          items={locations[location] || []}
          ambiguityNotice={
            ambiguityNotice && ambiguityNotice.location === location ? ambiguityNotice : null
          }
          userId={userId}
          userName={userName}
          onChanged={loadInventory}
        />
      ))}
      <RestockForm householdId={householdId} userId={userId} onRestocked={handleRestocked} />
    </div>
  );
}
