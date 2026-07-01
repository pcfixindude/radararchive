import { REPLAY_SHORTCUTS } from '../hooks/keyboardShortcuts';

export default function KeyboardShortcutsHelp() {
  return (
    <details className="keyboard-shortcuts-help">
      <summary>Keyboard shortcuts</summary>
      <ul>
        {REPLAY_SHORTCUTS.map((shortcut) => (
          <li key={shortcut.action}>
            <kbd>{shortcut.keys}</kbd> — {shortcut.description}
          </li>
        ))}
      </ul>
    </details>
  );
}
