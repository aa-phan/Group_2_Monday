import Availability from './Availability.js';
import Capacity from './Capacity.js';
import CheckIn from './CheckIn.js';
import CheckOut from './CheckOut.js';

/**
 * HardwareSet is one hardware set's card: its name plus four components --
 * Availability, Capacity, Check In, and Check Out.
 *
 * Data source: props only
 *
 * @component
 * @param {Object} props
 * @param {string} props.projectId - The project the set belongs to.
 * @param {string} props.userId - The acting member's id.
 * @param {Object} props.hwSet - `{ hwSetName, capacity, available }`.
 * @param {Function} props.onChanged - Async reload callback.
 */
export default function HardwareSet({ projectId, userId, hwSet, onChanged }) {
  return (
    <section className="hw-set" aria-label={hwSet.hwSetName}>
      <h2 className="hw-set__name">{hwSet.hwSetName}</h2>
      <div className="hw-set__grid">
        <Availability available={hwSet.available} />
        <Capacity capacity={hwSet.capacity} />
        <CheckIn
          projectId={projectId}
          userId={userId}
          hwSetName={hwSet.hwSetName}
          onChanged={onChanged}
        />
        <CheckOut
          projectId={projectId}
          userId={userId}
          hwSetName={hwSet.hwSetName}
          onChanged={onChanged}
        />
      </div>
    </section>
  );
}
