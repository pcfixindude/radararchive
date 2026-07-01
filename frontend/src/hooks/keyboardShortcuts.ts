export type ReplayShortcutAction =
  | 'togglePlay'
  | 'stepBackward'
  | 'stepForward'
  | 'toggleOverlay'
  | 'toggleBounds'
  | 'fitBounds'
  | 'setRangeStart'
  | 'setRangeEnd'
  | 'toggleLoopRange'
  | 'clearRange';

export type ReplayShortcut = {
  keys: string;
  action: ReplayShortcutAction;
  description: string;
};

export const REPLAY_SHORTCUTS: ReplayShortcut[] = [
  { keys: 'Space', action: 'togglePlay', description: 'Play / pause' },
  { keys: '← / →', action: 'stepBackward', description: 'Previous / next frame' },
  { keys: '[', action: 'setRangeStart', description: 'Set range start to current frame' },
  { keys: ']', action: 'setRangeEnd', description: 'Set range end to current frame' },
  { keys: 'L', action: 'toggleLoopRange', description: 'Toggle loop range' },
  { keys: 'Esc', action: 'clearRange', description: 'Clear playback range' },
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
  if (event.key === '[') {
    return 'setRangeStart';
  }
  if (event.key === ']') {
    return 'setRangeEnd';
  }
  if (event.key === 'l' || event.key === 'L') {
    return 'toggleLoopRange';
  }
  if (event.key === 'Escape') {
    return 'clearRange';
  }
  return null;
}

export function shouldPreventDefault(action: ReplayShortcutAction): boolean {
  return (
    action === 'togglePlay' ||
    action === 'stepBackward' ||
    action === 'stepForward' ||
    action === 'clearRange'
  );
}
