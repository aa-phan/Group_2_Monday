import { useCallback, useEffect, useState } from 'react';
import { fetchInventory } from '../api/inventory.js';
import FreshnessBadge from './FreshnessBadge.js';
import RestockForm from './RestockForm.js';

const LOCATION_ORDER = ['Pantry', 'Fridge', 'Freezer'];

function LocationSection({ location, items }) {
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
                <td>{item.itemName}</td>
                <td>{item.capacity}</td>
                <td>{item.availability}</td>
                <td>
                  <FreshnessBadge freshness={item.freshness} location={location} />
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
        <LocationSection key={location} location={location} items={locations[location] || []} />
      ))}
      <RestockForm householdId={householdId} userId={userId} onRestocked={loadInventory} />
    </div>
  );
}
