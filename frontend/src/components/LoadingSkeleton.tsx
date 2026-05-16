interface SkeletonProps {
  type?: 'card' | 'text' | 'title' | 'avatar' | 'table';
  count?: number;
}

export default function LoadingSkeleton({ type = 'card', count = 3 }: SkeletonProps) {
  if (type === 'text') {
    return (
      <div className="skeleton-group">
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className="skeleton skeleton-text"
            style={{ width: `${Math.random() * 40 + 60}%` }}
          />
        ))}
      </div>
    );
  }

  if (type === 'title') {
    return <div className="skeleton skeleton-title" />;
  }

  if (type === 'avatar') {
    return <div className="skeleton skeleton-avatar" />;
  }

  if (type === 'table') {
    return (
      <div className="skeleton-table">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="skeleton-table-row">
            <div className="skeleton skeleton-text" style={{ width: '20%' }} />
            <div className="skeleton skeleton-text" style={{ width: '30%' }} />
            <div className="skeleton skeleton-text" style={{ width: '15%' }} />
            <div className="skeleton skeleton-text" style={{ width: '25%' }} />
          </div>
        ))}
      </div>
    );
  }

  // Default: card skeletons
  return (
    <div className="skeleton-cards">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton skeleton-card" />
      ))}
    </div>
  );
}
