export function formatTimestampDisplay(iso: string): { utc: string; local: string } {
  if (!iso) {
    return { utc: '—', local: '—' };
  }
  const date = new Date(iso);
  return {
    utc: iso,
    local: Number.isNaN(date.getTime()) ? iso : date.toLocaleString(),
  };
}
