export type ReplayShortcutAction =
  | 'togglePlay'
  | 'stepBackward'
  | 'stepForward'
  | 'toggleOverlay'
  | 'toggleBounds'
  | 'fitBounds';

export type ReplayShortcut = {
  keys: string;
  action: ReplayShortcutAction;
  description: string;
};

export const REPLAY_SHORTCUTS: ReplayShortcut[] = [
  { keys: 'Space', action: 'togglePlay', description: 'Play / pause' },
  { keys: '← / →', action: 'stepBackward', description: 'Previous / next frame' },
  { keys: 'O', action: 'toggleOverlay', description: 'Toggle decoded overlay' },
  { keys: 'B', action: 'toggleBounds', description: 'Toggle bounds outline' },
  { keys: 'F', action: 'fitBounds', description: 'Fit map to overlay bounds' },
];

export function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) {
    return false;
  }
  const tag = target.tagName.toLowerCase();
  if (tag === 'input' || tag === 'textarea' || tag === 'select') {
    return true;
  }
  return target.isContentEditable;
}

export function resolveShortcutAction(event: KeyboardEvent): ReplayShortcutAction | null {
  if (isEditableTarget(event.target)) {
    return null;
  }
  if (event.key === ' ' || event.code === 'Space') {
    return 'togglePlay';
  }
  if (event.key === 'ArrowLeft') {
    return 'stepBackward';
  }
  if (event.key === 'ArrowRight') {
    return 'stepForward';
  }
  if (event.key === 'o' || event.key === 'O') {
    return 'toggleOverlay';
  }
  if (event.key === 'b' || event.key === 'B') {
    return 'toggleBounds';
  }
  if (event.key === 'f' || event.key === 'F') {
    return 'fitBounds';
  }
  return null;
}

export function shouldPreventDefault(action: ReplayShortcutAction): boolean {
  return action === 'togglePlay' || action === 'stepBackward' || action === 'stepForward';
}
