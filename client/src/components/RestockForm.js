import { useState } from 'react';
import { restockItem } from '../api/inventory.js';

const LOCATIONS = ['Pantry', 'Fridge', 'Freezer'];

function todayISODate() {
  return new Date().toISOString().slice(0, 10);
}

export default function RestockForm({ householdId, userId, onRestocked }) {
  const [itemName, setItemName] = useState('');
  const [location, setLocation] = useState(LOCATIONS[0]);
  const [quantity, setQuantity] = useState(1);
  const [purchaseDate, setPurchaseDate] = useState(todayISODate());
  const [bestByDate, setBestByDate] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      await restockItem({
        householdId,
        userId,
        location,
        itemName,
        quantity: Number(quantity),
        purchaseDate,
        bestByDate: bestByDate || null,
      });
      await onRestocked();
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="restock-form" onSubmit={handleSubmit}>
      <h3>Restock an item</h3>

      <label>
        Item name
        <input
          type="text"
          value={itemName}
          onChange={(event) => setItemName(event.target.value)}
          required
        />
      </label>

      <label>
        Location
        <select value={location} onChange={(event) => setLocation(event.target.value)}>
          {LOCATIONS.map((loc) => (
            <option key={loc} value={loc}>
              {loc}
            </option>
          ))}
        </select>
      </label>

      <label>
        Quantity
        <input
          type="number"
          min="1"
          value={quantity}
          onChange={(event) => setQuantity(event.target.value)}
          required
        />
      </label>

      <label>
        Purchase date
        <input
          type="date"
          value={purchaseDate}
          onChange={(event) => setPurchaseDate(event.target.value)}
          required
        />
      </label>

      <label>
        Best-by date
        <input
          type="date"
          value={bestByDate}
          onChange={(event) => setBestByDate(event.target.value)}
        />
      </label>

      <button type="submit" disabled={submitting}>
        {submitting ? 'Restocking...' : 'Restock'}
      </button>

      {error && <p className="error-text">{error}</p>}
    </form>
  );
}
