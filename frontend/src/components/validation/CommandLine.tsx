type CommandLineProps = {
  command?: string | null;
  label?: string;
};

export default function CommandLine({
  command,
  label = 'Suggested command',
}: CommandLineProps) {
  if (!command) {
    return null;
  }
  return (
    <p className="validation-meta">
      {label}: <code className="validation-command-line">{command}</code>
    </p>
  );
}
