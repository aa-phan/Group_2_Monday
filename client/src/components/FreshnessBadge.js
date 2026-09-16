/**
 * FreshnessBadge renders the server-computed `freshness` value for an item
 * or batch, worded per its `location` because the same value means
 * different things in different places (INV-05 / D-09, D-10, D-11).
 *
 * This component does no date arithmetic and imports no date library -- it
 * only formats a value the server already computed. Freezer's "expired"
 * band is deliberately worded as a quality signal ("Freezer burn risk"),
 * never a discard instruction or a safety warning, because frozen food
 * past twelve months is quality-degraded, not unsafe (D-11).
 */

const LABELS = {
  Pantry: {
    fresh: 'Fresh',
    expiring_soon: 'Use soon',
    expired: 'Past best-by',
  },
  Fridge: {
    fresh: 'Fresh',
    expiring_soon: 'Use soon',
    expired: 'Past best-by',
  },
  Freezer: {
    fresh: 'Good quality',
    expiring_soon: 'Quality declining',
    expired: 'Freezer burn risk',
  },
};

const TITLES = {
  Pantry: {
    fresh: "This item's best-by date has not passed.",
    expired: "This item's best-by date has passed.",
  },
  Fridge: {
    fresh: "This item's best-by date is more than 3 days away.",
    expiring_soon: "This item's best-by date is 3 or fewer days away.",
    expired: "This item's best-by date has passed.",
  },
  Freezer: {
    fresh: 'Frozen less than 6 months ago.',
    expiring_soon: 'Frozen 6 to 12 months ago — quality may be starting to decline.',
    expired: 'Frozen over 12 months ago — freezer-burn quality risk, still safe to eat.',
  },
};

const UNKNOWN_LABEL = 'No date';
const UNKNOWN_TITLE = 'No date was recorded for this batch, so freshness cannot be determined.';

export default function FreshnessBadge({ freshness, location }) {
  const locationLabels = LABELS[location] || {};
  const locationTitles = TITLES[location] || {};

  const label = freshness === 'unknown' ? UNKNOWN_LABEL : locationLabels[freshness] || UNKNOWN_LABEL;
  const title = freshness === 'unknown' ? UNKNOWN_TITLE : locationTitles[freshness] || UNKNOWN_TITLE;
  const freshnessClass = freshness || 'unknown';

  return (
    <span className={`freshness-badge freshness-badge--${freshnessClass}`} title={title}>
      {label}
    </span>
  );
}
