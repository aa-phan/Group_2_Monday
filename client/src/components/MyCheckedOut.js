/**
 * MyCheckedOut shows how many units of a hardware set the CURRENT project
 * (shared by every one of its members) has checked out right now -- not
 * the catalog-wide total (that's Availability/Capacity, shared by every
 * project). Checkin is capped at this number: any member of this project
 * can check in units a teammate on the SAME project checked out, but not
 * units checked out through a different project.
 *
 * Data source: props only
 *
 * @component
 * @param {Object} props
 * @param {number} props.myCheckedOut - Units this project collectively holds.
 */
export default function MyCheckedOut({ myCheckedOut }) {
  return (
    <div className="hw-cell">
      <span className="hw-cell__label">Checked Out</span>
      <span className="hw-cell__value">{myCheckedOut}</span>
    </div>
  );
}
