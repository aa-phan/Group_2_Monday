import { useState } from 'react';

/**
 * QuantityAction is the shared control behind Check In and Check Out: a
 * quantity input plus one action button, with its own busy and error state.
 *
 * Data source: calls the `action` prop
 *
 * @component
 * @param {Object} props
 * @param {string} props.label - Button text and input label, e.g. "Check Out".
 * @param {string} props.busyLabel - Button text while the call is in flight.
 * @param {Function} props.action - Async `(quantity: number) => void`; throws
 *   on failure.
 * @param {Function} props.describeError - `(error) => string` user-facing
 *   message for a failed action.
 * @param {Function} props.onChanged - Async reload callback, awaited after
 *   every successful action.
 */
export default function QuantityAction({ label, busyLabel, action, describeError, onChanged }) {
  const [quantity, setQuantity] = useState('1');
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await action(Number(quantity));
      await onChanged();
    } catch (actionError) {
      setError(describeError(actionError));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="hw-cell hw-action" onSubmit={handleSubmit}>
      <label className="hw-cell__label">
        {label}
        <input
          type="number"
          min="1"
          step="1"
          value={quantity}
          onChange={(event) => setQuantity(event.target.value)}
        />
      </label>
      <button type="submit" disabled={busy}>
        {busy ? busyLabel : label}
      </button>
      {error && (
        <p className="error-text hw-action__error" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
