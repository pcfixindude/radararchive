import { useState, type ReactNode } from 'react';

type CollapsibleSectionProps = {
  title: string;
  summary?: ReactNode;
  defaultExpanded?: boolean;
  expanded?: boolean;
  onExpandedChange?: (expanded: boolean) => void;
  className?: string;
  children: ReactNode;
};

export default function CollapsibleSection({
  title,
  summary,
  defaultExpanded = false,
  expanded: expandedProp,
  onExpandedChange,
  className,
  children,
}: CollapsibleSectionProps) {
  const [internalExpanded, setInternalExpanded] = useState(defaultExpanded);
  const expanded = expandedProp ?? internalExpanded;

  function toggleExpanded() {
    const next = !expanded;
    if (expandedProp === undefined) {
      setInternalExpanded(next);
    }
    onExpandedChange?.(next);
  }

  return (
    <section className={`validation-collapsible ${className ?? ''}`.trim()}>
      <div className="validation-collapsible-header">
        <button
          type="button"
          className="validation-collapsible-toggle"
          onClick={toggleExpanded}
          aria-expanded={expanded}
        >
          <span className="validation-collapsible-title">{title}</span>
          <span className="validation-collapsible-chevron" aria-hidden="true">
            {expanded ? '▼' : '▶'}
          </span>
        </button>
      </div>
      {summary ? <div className="validation-collapsible-summary">{summary}</div> : null}
      {expanded ? <div className="validation-collapsible-body">{children}</div> : null}
    </section>
  );
}
