import { describe, expect, it } from 'vitest';
import {
  isEditableTarget,
  resolveShortcutAction,
  shouldPreventDefault,
} from '../hooks/keyboardShortcuts';

describe('resolveShortcutAction', () => {
  it('maps space to toggle play', () => {
    const event = new KeyboardEvent('keydown', { key: ' ', code: 'Space' });
    expect(resolveShortcutAction(event)).toBe('togglePlay');
  });

  it('maps arrows to step actions', () => {
    expect(resolveShortcutAction(new KeyboardEvent('keydown', { key: 'ArrowLeft' }))).toBe(
      'stepBackward',
    );
    expect(resolveShortcutAction(new KeyboardEvent('keydown', { key: 'ArrowRight' }))).toBe(
      'stepForward',
    );
  });

  it('maps overlay and bounds toggles', () => {
    expect(resolveShortcutAction(new KeyboardEvent('keydown', { key: 'o' }))).toBe('toggleOverlay');
    expect(resolveShortcutAction(new KeyboardEvent('keydown', { key: 'B' }))).toBe('toggleBounds');
    expect(resolveShortcutAction(new KeyboardEvent('keydown', { key: 'f' }))).toBe('fitBounds');
  });

  it('maps range and loop shortcuts', () => {
    expect(resolveShortcutAction(new KeyboardEvent('keydown', { key: '[' }))).toBe('setRangeStart');
    expect(resolveShortcutAction(new KeyboardEvent('keydown', { key: ']' }))).toBe('setRangeEnd');
    expect(resolveShortcutAction(new KeyboardEvent('keydown', { key: 'l' }))).toBe('toggleLoopRange');
    expect(resolveShortcutAction(new KeyboardEvent('keydown', { key: 'Escape' }))).toBe('clearRange');
  });

  it('ignores shortcuts while typing in inputs', () => {
    const input = document.createElement('input');
    const event = new KeyboardEvent('keydown', { key: ' ', code: 'Space' });
    Object.defineProperty(event, 'target', { value: input });
    expect(resolveShortcutAction(event)).toBeNull();
    expect(isEditableTarget(input)).toBe(true);
  });
});

describe('shouldPreventDefault', () => {
  it('prevents default for playback keys', () => {
    expect(shouldPreventDefault('togglePlay')).toBe(true);
    expect(shouldPreventDefault('toggleOverlay')).toBe(false);
  });
});
