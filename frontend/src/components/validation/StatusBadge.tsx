type StatusBadgeProps = {
  level?: string | null;
};

export default function StatusBadge({ level }: StatusBadgeProps) {
  const normalized = (level ?? 'unknown').toLowerCase();
  return (
    <span className={`validation-status-badge validation-status-badge--${normalized}`}>
      {normalized}
    </span>
  );
}
