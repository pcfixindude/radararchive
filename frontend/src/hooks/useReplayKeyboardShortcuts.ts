import { useEffect } from 'react';
import {
  resolveShortcutAction,
  shouldPreventDefault,
  type ReplayShortcutAction,
} from './keyboardShortcuts';

export function useReplayKeyboardShortcuts({
  enabled,
  canStep,
  canFitBounds,
  onAction,
}: {
  enabled: boolean;
  canStep: boolean;
  canFitBounds: boolean;
  onAction: (action: ReplayShortcutAction) => void;
}) {
  useEffect(() => {
    if (!enabled) {
      return undefined;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      const action = resolveShortcutAction(event);
      if (!action) {
        return;
      }
      if ((action === 'stepBackward' || action === 'stepForward') && !canStep) {
        return;
      }
      if (action === 'fitBounds' && !canFitBounds) {
        return;
      }
      if (shouldPreventDefault(action)) {
        event.preventDefault();
      }
      onAction(action);
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [enabled, canStep, canFitBounds, onAction]);
}
