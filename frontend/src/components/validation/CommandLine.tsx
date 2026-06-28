type CommandLineProps = {
  command?: string | null;
  label?: string;
  manualCopy?: boolean;
};

export default function CommandLine({
  command,
  label = 'Suggested command',
  manualCopy = false,
}: CommandLineProps) {
  if (!command) {
    return null;
  }
  return (
    <div className="validation-command-block">
      {manualCopy ? (
        <p className="validation-meta validation-command-copy-hint">
          Copy this command manually — the Dev Validation UI does not run commands automatically.
        </p>
      ) : null}
      <p className="validation-meta">
        {label}: <code className="validation-command-line">{command}</code>
      </p>
    </div>
  );
}
