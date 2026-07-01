import { useEffect, useState } from 'react';
import { fetchIngestWindowPlan } from '../api/client';
import { ingestWindowQueryFromState } from '../components/ingestWindow';
import { bookmarkSummary, type ReplayBookmark } from '../hooks/replayBookmarks';

export default function ReplayBookmarksPanel({
  disabled = false,
  bookmarks,
  storageWarning = null,
  lastLoadedId = null,
  restoreHints = [],
  onSave,
  onLoad,
  onDelete,
  onRename,
}: {
  disabled?: boolean;
  bookmarks: ReplayBookmark[];
  storageWarning?: string | null;
  lastLoadedId?: string | null;
  restoreHints?: string[];
  onSave: (name: string) => void;
  onLoad: (id: string) => void;
  onDelete: (id: string) => void;
  onRename: (id: string, name: string) => void;
}) {
  const [name, setName] = useState('');
  const [renameId, setRenameId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [ingestCommand, setIngestCommand] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const selectedBookmark = bookmarks.find((bookmark) => bookmark.id === selectedId) ?? null;

  useEffect(() => {
    let cancelled = false;

    async function loadIngestCommand() {
      if (!selectedBookmark?.ingest) {
        setIngestCommand(null);
        return;
      }
      try {
        const plan = await fetchIngestWindowPlan(
          ingestWindowQueryFromState({
            preset: selectedBookmark.ingest.preset,
            limit: selectedBookmark.ingest.limit,
            warmCache: selectedBookmark.ingest.warmCache,
            customStart: selectedBookmark.ingest.customStart,
            customEnd: selectedBookmark.ingest.customEnd,
            replayStart: selectedBookmark.ingest.replayStart,
            replayEnd: selectedBookmark.ingest.replayEnd,
          }),
        );
        if (!cancelled) {
          setIngestCommand(plan.bulk_ingest_command);
        }
      } catch {
        if (!cancelled) {
          setIngestCommand(null);
        }
      }
    }

    loadIngestCommand();
    return () => {
      cancelled = true;
    };
  }, [selectedBookmark]);

  const handleSave = () => {
    if (!name.trim()) {
      return;
    }
    onSave(name.trim());
    setName('');
  };

  const copyIngestCommand = async () => {
    if (!ingestCommand) {
      return;
    }
    try {
      await navigator.clipboard.writeText(ingestCommand);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  return (
    <section className="panel replay-bookmarks-panel" aria-label="Replay bookmarks">
      <h2>Bookmarks</h2>
      <p className="replay-bookmarks-intro">
        Save storm-segment replay setup in this browser. Bookmarks stay local — no cloud sync.
      </p>
      <div className="replay-bookmarks-save">
        <input
          type="text"
          placeholder="Bookmark name"
          disabled={disabled}
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
        <button type="button" disabled={disabled || !name.trim()} onClick={handleSave}>
          Save current setup
        </button>
      </div>
      {storageWarning ? <p className="replay-bookmarks-warning">{storageWarning}</p> : null}
      {restoreHints.length ? (
        <ul className="replay-bookmarks-hints">
          {restoreHints.map((hint) => (
            <li key={hint}>{hint}</li>
          ))}
        </ul>
      ) : null}
      {bookmarks.length === 0 ? (
        <p className="replay-bookmarks-empty">No bookmarks yet — set a range, then save.</p>
      ) : (
        <ul className="replay-bookmarks-list">
          {bookmarks.map((bookmark) => (
            <li
              key={bookmark.id}
              className={`replay-bookmark-item${bookmark.id === lastLoadedId ? ' replay-bookmark-item--active' : ''}`}
            >
              {renameId === bookmark.id ? (
                <div className="replay-bookmark-rename">
                  <input
                    type="text"
                    value={renameValue}
                    onChange={(event) => setRenameValue(event.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      onRename(bookmark.id, renameValue);
                      setRenameId(null);
                    }}
                  >
                    Save
                  </button>
                  <button type="button" onClick={() => setRenameId(null)}>
                    Cancel
                  </button>
                </div>
              ) : (
                <>
                  <div className="replay-bookmark-meta">
                    <strong>{bookmark.name}</strong>
                    <span>{bookmarkSummary(bookmark)}</span>
                  </div>
                  <div className="replay-bookmark-actions">
                    <button type="button" disabled={disabled} onClick={() => onLoad(bookmark.id)}>
                      Load
                    </button>
                    <button
                      type="button"
                      disabled={disabled}
                      onClick={() => {
                        setRenameId(bookmark.id);
                        setRenameValue(bookmark.name);
                      }}
                    >
                      Rename
                    </button>
                    <button
                      type="button"
                      disabled={disabled}
                      onClick={() => {
                        if (selectedId === bookmark.id) {
                          setSelectedId(null);
                        }
                        onDelete(bookmark.id);
                      }}
                    >
                      Delete
                    </button>
                    {bookmark.ingest ? (
                      <button
                        type="button"
                        onClick={() =>
                          setSelectedId((current) => (current === bookmark.id ? null : bookmark.id))
                        }
                      >
                        {selectedId === bookmark.id ? 'Hide command' : 'Ingest cmd'}
                      </button>
                    ) : null}
                  </div>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
      {selectedBookmark?.ingest && ingestCommand ? (
        <div className="replay-bookmark-command">
          <p className="replay-bookmark-command-label">
            Ingest command for <strong>{selectedBookmark.name}</strong>:
          </p>
          <code>{ingestCommand}</code>
          <button type="button" onClick={copyIngestCommand}>
            {copied ? 'Copied' : 'Copy command'}
          </button>
        </div>
      ) : null}
    </section>
  );
}
