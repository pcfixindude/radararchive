type SafetyNoteProps = {
  variant?: 'warn' | 'meta';
  compact?: boolean;
};

export default function SafetyNote({ variant = 'warn', compact = false }: SafetyNoteProps) {
  const className = variant === 'warn' ? 'validation-warn' : 'validation-meta';
  const text = compact
    ? 'Local only — not verified MRMS'
    : 'Local only — does not verify MRMS — does not clear alerts — does not enable production rendering';
  return <p className={className}>{text}</p>;
}
