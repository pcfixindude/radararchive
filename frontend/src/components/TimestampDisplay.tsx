import { formatTimestampDisplay } from '../utils/timeDisplay';

export default function TimestampDisplay({
  timestamp,
  processedCount,
  totalCount,
}: {
  timestamp: string;
  processedCount: number;
  totalCount: number;
}) {
  const { utc, local } = formatTimestampDisplay(timestamp);

  return (
    <section className="panel timestamp-panel">
      <h2>Selected Time</h2>
      <p className="timestamp-local">{local}</p>
      <p className="timestamp-utc">UTC: {utc}</p>
      <p className="timestamp-meta">
        Processed frames: {processedCount} / {totalCount}
      </p>
    </section>
  );
}
