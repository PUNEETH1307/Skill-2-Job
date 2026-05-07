interface SummaryCardProps {
  label: string;
  value: string | number;
  highlight?: boolean;
}

/**
 * Reusable summary card component for displaying a single metric.
 * Used across Student, Coordinator, and Admin dashboards.
 *
 * Validates: Requirements 4.3, 7.3
 */
export default function SummaryCard({ label, value, highlight = false }: SummaryCardProps) {
  const className = [
    'dash-card',
    'dash-summary-card',
    highlight ? 'dash-card-highlight' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <article className={className} aria-label={`${label}: ${value}`}>
      <h3 className="dash-summary-card-label">{label}</h3>
      <p className="dash-summary-card-value">{value}</p>
    </article>
  );
}
