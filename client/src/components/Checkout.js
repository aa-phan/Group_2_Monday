import { useState } from 'react';
import { consumeItem, reserveItem, releaseReservation } from '../api/inventory.js';

// The name "Checkout.js" carries over from the assignment's checkout
// mockup, which maps onto consuming (see plan 02-04). This component also
// renders reserve and release -- everything a household member does to an
// item's own row besides restocking.
//
// A reservation is a coordination signal among housemates ("dibs"), never
// a lock (D-05, D-07). The consume control below is never disabled, hidden,
// or gated by the presence of any reservation, and the reserved display
// below only ever names who claimed what -- it never says "unavailable",
// "locked", or "blocked".
export default function ItemActions({ item, userId, userName, onChanged }) {
  const [consumeQuantity, setConsumeQuantity] = useState('1');
  const [reserveQuantity, setReserveQuantity] = useState('1');
  const [consumeError, setConsumeError] = useState(null);
  const [reserveError, setReserveError] = useState(null);
  const [releaseError, setReleaseError] = useState(null);
  const [consuming, setConsuming] = useState(false);
  const [claimInFlight, setClaimInFlight] = useState(false);
  const [releaseTargetId, setReleaseTargetId] = useState(null);

  async function handleConsume(event) {
    event.preventDefault();
    setConsumeError(null);
    setConsuming(true);
    try {
      await consumeItem({
        householdId: item.householdId,
        userId,
        location: item.location,
        itemName: item.itemName,
        quantity: Number(consumeQuantity),
      });
      // Leave the entered quantity in place on success too -- a member
      // consuming the same amount repeatedly (e.g. "1 cup" at a time)
      // shouldn't have to retype it every time.
      await onChanged();
    } catch (error) {
      if (typeof error.onHand === 'number') {
        setConsumeError(
          `Only ${error.onHand} on hand -- can't consume ${error.requested}. Try a smaller amount.`
        );
      } else {
        setConsumeError(error.message);
      }
    } finally {
      setConsuming(false);
    }
  }

  async function handleReserve(event) {
    event.preventDefault();
    setReserveError(null);
    setClaimInFlight(true);
    try {
      await reserveItem({
        householdId: item.householdId,
        userId,
        userName,
        location: item.location,
        itemName: item.itemName,
        quantity: Number(reserveQuantity),
      });
      await onChanged();
    } catch (error) {
      setReserveError(error.message);
    } finally {
      setClaimInFlight(false);
    }
  }

  async function handleRelease(targetId) {
    setReleaseError(null);
    setReleaseTargetId(targetId);
    try {
      await releaseReservation({
        householdId: item.householdId,
        userId,
        reservationId: targetId,
      });
      await onChanged();
    } catch (error) {
      setReleaseError(error.message);
    } finally {
      setReleaseTargetId(null);
    }
  }

  const reservations = item.reservations || [];
  const reservedTotal = item.reservedQuantity || 0;
  const overReserved = reservedTotal > item.capacity;

  return (
    // Clicking inside these controls must not toggle the surrounding
    // <details> disclosure the item row lives in.
    <div className="item-actions" onClick={(event) => event.stopPropagation()}>
      <form className="item-actions__row" onSubmit={handleConsume}>
        <label className="item-actions__field">
          Consume
          <input
            type="number"
            min="1"
            value={consumeQuantity}
            onChange={(event) => setConsumeQuantity(event.target.value)}
          />
        </label>
        <button type="submit" disabled={consuming}>
          {consuming ? 'Consuming...' : 'Consume'}
        </button>
      </form>
      {consumeError && <p className="error-text item-actions__message">{consumeError}</p>}

      <form className="item-actions__row" onSubmit={handleReserve}>
        <label className="item-actions__field">
          Reserve
          <input
            type="number"
            min="1"
            value={reserveQuantity}
            onChange={(event) => setReserveQuantity(event.target.value)}
          />
        </label>
        <button type="submit" disabled={claimInFlight}>
          {claimInFlight ? 'Reserving...' : 'Reserve'}
        </button>
      </form>
      {reserveError && <p className="error-text item-actions__message">{reserveError}</p>}

      <div className="item-actions__reservations">
        {reservations.length === 0 ? (
          <p className="muted-text">No one has reserved this item.</p>
        ) : (
          <ul className="reservation-list">
            {reservations.map((entry) => {
              const entryId = entry.reservationId;
              const isThisRowPending = releaseTargetId === entryId;
              return (
                <li
                  key={entryId}
                  className={
                    entry.userId === userId
                      ? 'reservation-entry reservation-entry--own'
                      : 'reservation-entry reservation-entry--other'
                  }
                >
                  <span className="reservation-entry__label">
                    Reserved by {entry.userName}: {entry.quantity}
                  </span>
                  {entry.userId === userId && (
                    <button
                      type="button"
                      className="reservation-entry__release"
                      onClick={() => handleRelease(entryId)}
                      disabled={isThisRowPending}
                    >
                      {isThisRowPending ? 'Releasing...' : 'Release'}
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        )}
        {overReserved && (
          <p className="muted-text item-actions__over-reserved">
            {reservedTotal} reserved of {item.capacity} on hand -- reserving is a coordination
            signal, not a hold, so this is expected.
          </p>
        )}
      </div>
      {releaseError && <p className="error-text item-actions__message">{releaseError}</p>}
    </div>
  );
}
