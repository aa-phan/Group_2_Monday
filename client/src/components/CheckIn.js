import { checkinHardware } from '../api/hardware.js';
import QuantityAction from './QuantityAction.js';

function describeCheckinError(error) {
  if (typeof error.checkedOut === 'number') {
    return `Only ${error.checkedOut} checked out -- can't check in ${error.requested}.`;
  }
  if (error.field === 'quantity') {
    return 'Enter a whole number of 1 or more.';
  }
  return error.message;
}

/**
 * CheckIn returns a quantity of one hardware set, raising its availability.
 *
 * Data source: mutates via client/src/api/hardware.js
 *
 * @component
 * @param {Object} props
 * @param {string} props.projectId - The project the set belongs to.
 * @param {string} props.userId - The acting member's id.
 * @param {string} props.hwSetName - The hardware set to check in.
 * @param {Function} props.onChanged - Async reload callback.
 */
export default function CheckIn({ projectId, userId, hwSetName, onChanged }) {
  return (
    <QuantityAction
      label="Check In"
      busyLabel="Checking in..."
      action={(quantity) => checkinHardware({ projectId, userId, hwSetName, quantity })}
      describeError={describeCheckinError}
      onChanged={onChanged}
    />
  );
}
