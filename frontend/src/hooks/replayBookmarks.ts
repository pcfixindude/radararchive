import {
  DEFAULT_INGEST_WINDOW_STATE,
  type IngestWindowFormState,
  type IngestWindowPreset,
} from '../components/ingestWindow';

export const REPLAY_BOOKMARKS_STORAGE_KEY = 'radararchive.replayBookmarks.v1';
export const REPLAY_BOOKMARKS_SCHEMA_VERSION = 1;
export const MAX_REPLAY_BOOKMARKS = 20;

export type ReplayBookmarkIngest = {
  preset: IngestWindowPreset;
  limit: number;
  warmCache: boolean;
  customStart: string;
  customEnd: string;
  replayStart: string | null;
  replayEnd: string | null;
};

export type ReplayBookmark = {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  selectedLayer: string;
  selectedTime: string | null;
  rangeStart: string | null;
  rangeEnd: string | null;
  loopRange: boolean;
  ingest: ReplayBookmarkIngest | null;
};

export type ReplayBookmarksStore = {
  schemaVersion: number;
  bookmarks: ReplayBookmark[];
};

export type ReplayBookmarkSnapshot = {
  selectedLayer: string;
  selectedTime: string | null;
  rangeStart: string | null;
  rangeEnd: string | null;
  loopRange: boolean;
  ingest: IngestWindowFormState;
};

export type BookmarkRestorePlan = {
  selectedLayer: string;
  selectedTime: string | null;
  rangeStart: string | null;
  rangeEnd: string | null;
  loopRange: boolean;
  ingest: IngestWindowFormState;
  hints: string[];
};

function utcNow(): string {
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isIsoTimestamp(value: unknown): value is string {
  if (typeof value !== 'string') {
    return false;
  }
  return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(value);
}

function normalizeIsoTimestamp(value: string): string {
  return value.replace(/\.\d{3}Z$/, 'Z');
}

function isIngestPreset(value: unknown): value is IngestWindowPreset {
  return (
    value === 'last_1h' ||
    value === 'last_3h' ||
    value === 'last_6h' ||
    value === 'custom' ||
    value === 'replay_range'
  );
}

export function normalizeIngestBookmark(ingest: unknown): ReplayBookmarkIngest | null {
  if (!isRecord(ingest)) {
    return null;
  }
  if (!isIngestPreset(ingest.preset)) {
    return null;
  }
  const limit = Number(ingest.limit);
  return {
    preset: ingest.preset,
    limit: Number.isFinite(limit) ? Math.max(1, Math.min(20, limit)) : 8,
    warmCache: Boolean(ingest.warmCache),
    customStart: typeof ingest.customStart === 'string' ? ingest.customStart : '',
    customEnd: typeof ingest.customEnd === 'string' ? ingest.customEnd : '',
    replayStart: typeof ingest.replayStart === 'string' ? ingest.replayStart : null,
    replayEnd: typeof ingest.replayEnd === 'string' ? ingest.replayEnd : null,
  };
}

export function ingestBookmarkToFormState(ingest: ReplayBookmarkIngest | null): IngestWindowFormState {
  if (!ingest) {
    return DEFAULT_INGEST_WINDOW_STATE;
  }
  return {
    preset: ingest.preset,
    limit: ingest.limit,
    warmCache: ingest.warmCache,
    customStart: ingest.customStart,
    customEnd: ingest.customEnd,
    replayStart: ingest.replayStart,
    replayEnd: ingest.replayEnd,
  };
}

export function ingestFormToBookmark(ingest: IngestWindowFormState): ReplayBookmarkIngest {
  return {
    preset: ingest.preset,
    limit: ingest.limit,
    warmCache: ingest.warmCache,
    customStart: ingest.customStart,
    customEnd: ingest.customEnd,
    replayStart: ingest.replayStart,
    replayEnd: ingest.replayEnd,
  };
}

export function validateBookmark(value: unknown): ReplayBookmark | null {
  if (!isRecord(value)) {
    return null;
  }
  if (typeof value.id !== 'string' || !value.id.trim()) {
    return null;
  }
  if (typeof value.name !== 'string' || !value.name.trim()) {
    return null;
  }
  if (!isIsoTimestamp(value.createdAt) || !isIsoTimestamp(value.updatedAt)) {
    return null;
  }
  if (typeof value.selectedLayer !== 'string' || !value.selectedLayer.trim()) {
    return null;
  }
  const selectedTime = value.selectedTime === null || isIsoTimestamp(value.selectedTime) ? value.selectedTime : null;
  const rangeStart = value.rangeStart === null || isIsoTimestamp(value.rangeStart) ? value.rangeStart : null;
  const rangeEnd = value.rangeEnd === null || isIsoTimestamp(value.rangeEnd) ? value.rangeEnd : null;
  const ingest = value.ingest === null ? null : normalizeIngestBookmark(value.ingest);

  return {
    id: value.id,
    name: value.name.trim(),
    createdAt: normalizeIsoTimestamp(value.createdAt),
    updatedAt: normalizeIsoTimestamp(value.updatedAt),
    selectedLayer: value.selectedLayer,
    selectedTime: selectedTime ? normalizeIsoTimestamp(selectedTime) : null,
    rangeStart: rangeStart ? normalizeIsoTimestamp(rangeStart) : null,
    rangeEnd: rangeEnd ? normalizeIsoTimestamp(rangeEnd) : null,
    loopRange: Boolean(value.loopRange),
    ingest,
  };
}

export function emptyBookmarksStore(): ReplayBookmarksStore {
  return { schemaVersion: REPLAY_BOOKMARKS_SCHEMA_VERSION, bookmarks: [] };
}

export function parseBookmarksStore(raw: string | null): ReplayBookmarksStore {
  if (!raw) {
    return emptyBookmarksStore();
  }
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!isRecord(parsed)) {
      return emptyBookmarksStore();
    }
    if (parsed.schemaVersion !== REPLAY_BOOKMARKS_SCHEMA_VERSION) {
      return emptyBookmarksStore();
    }
    if (!Array.isArray(parsed.bookmarks)) {
      return emptyBookmarksStore();
    }
    const bookmarks = parsed.bookmarks
      .map((item) => validateBookmark(item))
      .filter((item): item is ReplayBookmark => item !== null)
      .slice(0, MAX_REPLAY_BOOKMARKS);
    return { schemaVersion: REPLAY_BOOKMARKS_SCHEMA_VERSION, bookmarks };
  } catch {
    return emptyBookmarksStore();
  }
}

export function serializeBookmarksStore(store: ReplayBookmarksStore): string {
  return JSON.stringify({
    schemaVersion: REPLAY_BOOKMARKS_SCHEMA_VERSION,
    bookmarks: store.bookmarks.slice(0, MAX_REPLAY_BOOKMARKS),
  });
}

export function readBookmarksStore(storage: Storage = localStorage): ReplayBookmarksStore {
  return parseBookmarksStore(storage.getItem(REPLAY_BOOKMARKS_STORAGE_KEY));
}

export function writeBookmarksStore(
  store: ReplayBookmarksStore,
  storage: Storage = localStorage,
): ReplayBookmarksStore {
  const bounded = {
    schemaVersion: REPLAY_BOOKMARKS_SCHEMA_VERSION,
    bookmarks: store.bookmarks.slice(0, MAX_REPLAY_BOOKMARKS),
  };
  storage.setItem(REPLAY_BOOKMARKS_STORAGE_KEY, serializeBookmarksStore(bounded));
  return bounded;
}

export function createBookmarkId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `bookmark-${Date.now()}`;
}

export function createBookmarkFromSnapshot(
  name: string,
  snapshot: ReplayBookmarkSnapshot,
): ReplayBookmark {
  const now = utcNow();
  return {
    id: createBookmarkId(),
    name: name.trim(),
    createdAt: now,
    updatedAt: now,
    selectedLayer: snapshot.selectedLayer,
    selectedTime: snapshot.selectedTime,
    rangeStart: snapshot.rangeStart,
    rangeEnd: snapshot.rangeEnd,
    loopRange: snapshot.loopRange,
    ingest: ingestFormToBookmark(snapshot.ingest),
  };
}

export function resolveRestoreSelectedTime(
  bookmark: ReplayBookmark,
  playbackTimes: string[],
): string | null {
  if (bookmark.selectedTime && playbackTimes.includes(bookmark.selectedTime)) {
    return bookmark.selectedTime;
  }
  if (bookmark.rangeStart && playbackTimes.includes(bookmark.rangeStart)) {
    return bookmark.rangeStart;
  }
  if (bookmark.rangeEnd && playbackTimes.includes(bookmark.rangeEnd)) {
    return bookmark.rangeEnd;
  }
  return null;
}

export function buildBookmarkRestorePlan(
  bookmark: ReplayBookmark,
  playbackTimes: string[],
): BookmarkRestorePlan {
  const hints: string[] = [];
  const ingest = ingestBookmarkToFormState(bookmark.ingest);
  const restoredTime = resolveRestoreSelectedTime(bookmark, playbackTimes);

  if (!restoredTime) {
    hints.push('Saved frame timestamps are not in the current timeline — ingest/warm/decode may be needed.');
  }
  if (bookmark.rangeStart && !playbackTimes.includes(bookmark.rangeStart)) {
    hints.push('Range start is not loaded yet — range values restored for when frames appear.');
  }
  if (bookmark.rangeEnd && !playbackTimes.includes(bookmark.rangeEnd)) {
    hints.push('Range end is not loaded yet — copy the ingest command if frames are missing.');
  }
  if (bookmark.loopRange && (!bookmark.rangeStart || !bookmark.rangeEnd)) {
    hints.push('Loop was saved but range endpoints are incomplete.');
  }

  return {
    selectedLayer: bookmark.selectedLayer,
    selectedTime: restoredTime,
    rangeStart: bookmark.rangeStart,
    rangeEnd: bookmark.rangeEnd,
    loopRange: bookmark.loopRange,
    ingest,
    hints,
  };
}

export function bookmarkSummary(bookmark: ReplayBookmark): string {
  const parts: string[] = [];
  if (bookmark.rangeStart && bookmark.rangeEnd) {
    parts.push(`${bookmark.rangeStart} → ${bookmark.rangeEnd}`);
  }
  if (bookmark.loopRange) {
    parts.push('loop on');
  }
  if (bookmark.ingest?.preset) {
    parts.push(`ingest ${bookmark.ingest.preset}`);
  }
  return parts.length ? parts.join(' · ') : 'No range saved';
}
