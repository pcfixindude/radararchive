import { useState } from 'react';
import { copyTextToClipboard } from './copyText';

type CommandLineProps = {
  command?: string | null;
  label?: string;
  manualCopy?: boolean;
};

type CopyState = 'idle' | 'copied' | 'error';

export default function CommandLine({
  command,
  label = 'Suggested command',
  manualCopy = false,
}: CommandLineProps) {
  const [copyState, setCopyState] = useState<CopyState>('idle');

  if (!command) {
    return null;
  }

  async function handleCopy() {
    const copied = await copyTextToClipboard(command ?? '');
    setCopyState(copied ? 'copied' : 'error');
    if (copied) {
      window.setTimeout(() => setCopyState('idle'), 2000);
    }
  }

  const copyLabel =
    copyState === 'copied' ? 'Copied' : copyState === 'error' ? 'Copy failed' : 'Copy';

  return (
    <div className="validation-command-block">
      {manualCopy ? (
        <p className="validation-meta validation-command-copy-hint">
          Copy pastes the command to your clipboard — it does not run commands. Paste into your
          terminal manually.
        </p>
      ) : null}
      <p className="validation-meta validation-command-label">{label}</p>
      <div className="validation-command-row">
        <code className="validation-command-line">{command}</code>
        <button
          type="button"
          className="validation-copy-button"
          onClick={() => void handleCopy()}
          aria-label={`Copy ${label}`}
        >
          {copyLabel}
        </button>
      </div>
      {copyState === 'error' ? (
        <p className="validation-meta validation-command-copy-fallback">
          Clipboard unavailable — select the command text above and copy manually.
        </p>
      ) : null}
    </div>
  );
}
