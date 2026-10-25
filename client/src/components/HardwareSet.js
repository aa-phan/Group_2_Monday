import Availability from './Availability.js';
import Capacity from './Capacity.js';
import MyCheckedOut from './MyCheckedOut.js';
import CheckIn from './CheckIn.js';
import CheckOut from './CheckOut.js';

/**
 * HardwareSet is one hardware set's card: its name plus five components --
 * Availability, Capacity, My Checked Out, Check In, and Check Out.
 *
 * Data source: props only
 *
 * @component
 * @param {Object} props
 * @param {string} props.projectId - The project the set belongs to.
 * @param {string} props.userId - The acting member's id.
 * @param {Object} props.hwSet - `{ hwSetName, capacity, available,
 *   myCheckedOut }`. myCheckedOut is this user's own holding (server-
 *   tracked per user), not derived from capacity/available -- those are
 *   project-wide and say nothing about who personally holds what.
 * @param {Function} props.onChanged - Async reload callback.
 */
export default function HardwareSet({ projectId, userId, hwSet, onChanged }) {
  return (
    <section className="hw-set" aria-label={hwSet.hwSetName}>
      <h2 className="hw-set__name">{hwSet.hwSetName}</h2>
      <div className="hw-set__grid">
        <Availability available={hwSet.available} />
        <Capacity capacity={hwSet.capacity} />
        <MyCheckedOut myCheckedOut={hwSet.myCheckedOut} />
        <CheckIn
          projectId={projectId}
          userId={userId}
          hwSetName={hwSet.hwSetName}
          checkedOut={hwSet.myCheckedOut}
          onChanged={onChanged}
        />
        <CheckOut
          projectId={projectId}
          userId={userId}
          hwSetName={hwSet.hwSetName}
          available={hwSet.available}
          onChanged={onChanged}
        />
      </div>
    </section>
  );
}
