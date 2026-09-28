import { useCallback, useEffect, useState } from 'react';
import { fetchInventory } from '../api/inventory.js';
import BatchList from './BatchList.js';
import FreshnessBadge from './FreshnessBadge.js';
import ItemActions from './Checkout.js';
import RestockForm from './RestockForm.js';
import Modal from './Modal.js';

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
 * InventoryTable renders every location's items flattened into a single row
 * set -- replaces Phase 5's three per-location `LocationSection` card lists.
 *
 * Data source: props only
 * No hard-coded fallback: this component renders nothing it was not given or told.
 *
 * @component
 * @param {Object} props
 * @param {Array} props.rows - `{ item, location }` pairs, one per item
 *   across all locations, in `LOCATION_ORDER` sequence.
 * @param {Function} props.onRowClick - Called with the clicked row when a
 *   household member wants that item's detail.
 */
function InventoryTable({ rows, onRowClick }) {
  return (
    <div className="inventory-table-wrap">
      <table className="inventory-table">
        <thead>
          <tr>
            <th>Location</th>
            <th>Item</th>
            <th>Capacity</th>
            <th>Available</th>
            <th>Freshness</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const { item, location } = row;
            return (
              <tr
                key={`${location}:${item.itemKey}`}
                className="inventory-table__row"
                onClick={() => onRowClick(row)}
              >
                <td>{location}</td>
                <td>
                  <button type="button" className="inventory-table__open" aria-haspopup="dialog">
                    {item.itemName}
                  </button>
                </td>
                <td className="inventory-table__num">{item.capacity}</td>
                <td className="inventory-table__num">{item.availability}</td>
                <td>
                  <FreshnessBadge freshness={item.freshness} location={location} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/**
 * InventoryView is the top-level presentational component for a household's
 * inventory. It fetches its own inventory data through
 * client/src/api/inventory.js, but accepts session identity as props rather
 * than reading it from any global auth state -- Track A's session/auth layer
 * wires real values in here once it lands.
 *
 * See .planning/phases/05-ui-design/05-DESIGN.md for the data contract and
 * .planning/phases/06-track-e-visual-design-polish/06-UI-SPEC.md for the
 * dashboard layout this component now renders.
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
  const [openModal, setOpenModal] = useState(null);

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

  const rows = LOCATION_ORDER.flatMap((location) =>
    (locations[location] || []).map((item) => ({ item, location }))
  );

  return (
    <div>
      <InventoryTable
        rows={rows}
        onRowClick={(row) =>
          setOpenModal({ kind: 'detail', item: row.item, location: row.location })
        }
      />
      <RestockForm householdId={householdId} userId={userId} onRestocked={handleRestocked} />
      {openModal && openModal.kind === 'detail' && (
        <Modal title={openModal.item.itemName} onClose={() => setOpenModal(null)}>
          <p className="item-detail__summary">
            {openModal.location} &middot; Capacity {openModal.item.capacity} &middot; Available{' '}
            {openModal.item.availability} &middot;{' '}
            <FreshnessBadge freshness={openModal.item.freshness} location={openModal.location} />
          </p>
          <BatchList batches={openModal.item.batches} location={openModal.location} />
          <ItemActions
            item={openModal.item}
            userId={userId}
            userName={userName}
            onChanged={loadInventory}
          />
        </Modal>
      )}
    </div>
  );
}
