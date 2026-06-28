export function yesNo(value: boolean): string {
  return value ? 'yes' : 'no';
}

export function formatTimestamp(value: string | null | undefined): string {
  if (!value) {
    return '—';
  }
  return value.replace('T', ' ').replace('Z', ' UTC');
}
