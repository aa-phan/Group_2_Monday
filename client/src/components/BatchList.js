import FreshnessBadge from './FreshnessBadge.js';

/**
 * BatchList renders one item's batch history -- one row per shopping trip,
 * each with its own quantity, purchase date, best-by date, and freshness.
 *
 * `batches` MUST be rendered in the order it is received. The server
 * already returns batches in consumption order (soonest best-by first for
 * Pantry/Fridge, oldest purchase date first for Freezer, per D-02/D-11 and
 * hardwareDatabase's _batchSortKey) -- re-sorting here in the browser would
 * show a household the wrong thing about what gets used first.
 */
export default function BatchList({ batches, location }) {
  return (
    <div className="batch-list">
      <p className="batch-list__note">Batches are listed in the order they will be used.</p>
      <ul className="batch-card-list">
        {batches.map((batch) => (
          <li key={batch.batchId} className="batch-card">
            <div className="batch-card__field">
              <span className="batch-card__label">Quantity</span>
              <span className="batch-card__value">{batch.quantity}</span>
            </div>
            <div className="batch-card__field">
              <span className="batch-card__label">Purchased</span>
              <span className="batch-card__value">{batch.purchaseDate}</span>
            </div>
            <div className="batch-card__field">
              <span className="batch-card__label">Best-by</span>
              <span className="batch-card__value">{batch.bestByDate || '—'}</span>
            </div>
            <div className="batch-card__field">
              <span className="batch-card__label">Freshness</span>
              <span className="batch-card__value">
                <FreshnessBadge freshness={batch.freshness} location={location} />
              </span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
