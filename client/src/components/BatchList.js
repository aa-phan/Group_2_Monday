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
      <table className="batch-table">
        <thead>
          <tr>
            <th>Quantity</th>
            <th>Purchased</th>
            <th>Best-by</th>
            <th>Freshness</th>
          </tr>
        </thead>
        <tbody>
          {batches.map((batch) => (
            <tr key={batch.batchId}>
              <td>{batch.quantity}</td>
              <td>{batch.purchaseDate}</td>
              <td>{batch.bestByDate || '—'}</td>
              <td>
                <FreshnessBadge freshness={batch.freshness} location={location} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
