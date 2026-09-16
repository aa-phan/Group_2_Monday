import { useCallback, useEffect, useState } from 'react';
import { fetchInventory } from '../api/inventory.js';
import BatchList from './BatchList.js';
import FreshnessBadge from './FreshnessBadge.js';
import RestockForm from './RestockForm.js';

const LOCATION_ORDER = ['Pantry', 'Fridge', 'Freezer'];

function AmbiguityNotice({ notice }) {
  return (
    <p className="ambiguity-notice">
      &quot;{notice.itemName}&quot; wasn&apos;t merged into an existing item because it could
      match more than one: {notice.candidates.join(', ')}. A separate item was created instead.
    </p>
  );
}

function LocationSection({ location, items, ambiguityNotice }) {
  return (
    <section className="location-section">
      <h2>{location}</h2>
      {items.length === 0 ? (
        <p className="muted-text">Nothing stored here yet.</p>
      ) : (
        <table className="item-table">
          <thead>
            <tr>
              <th>Item</th>
              <th>Capacity</th>
              <th>Availability</th>
              <th>Freshness</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.itemKey}>
                <td colSpan={4} className="item-row-cell">
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
                  </details>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

export default function InventoryView({ householdId, userId }) {
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
        />
      ))}
      <RestockForm householdId={householdId} userId={userId} onRestocked={handleRestocked} />
    </div>
  );
}
