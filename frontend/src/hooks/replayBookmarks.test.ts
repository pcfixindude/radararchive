import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  buildBookmarkRestorePlan,
  createBookmarkFromSnapshot,
  emptyBookmarksStore,
  parseBookmarksStore,
  readBookmarksStore,
  REPLAY_BOOKMARKS_STORAGE_KEY,
  resolveRestoreSelectedTime,
  serializeBookmarksStore,
  validateBookmark,
  writeBookmarksStore,
} from './replayBookmarks';
import { DEFAULT_INGEST_WINDOW_STATE } from '../components/ingestWindow';

class MemoryStorage implements Storage {
  private data = new Map<string, string>();

  get length() {
    return this.data.size;
  }

  clear(): void {
    this.data.clear();
  }

  getItem(key: string): string | null {
    return this.data.get(key) ?? null;
  }

  key(index: number): string | null {
    return Array.from(this.data.keys())[index] ?? null;
  }

  removeItem(key: string): void {
    this.data.delete(key);
  }

  setItem(key: string, value: string): void {
    this.data.set(key, value);
  }
}

const sampleSnapshot = {
  selectedLayer: 'mrms_reflectivity',
  selectedTime: '2026-06-28T13:00:00Z',
  rangeStart: '2026-06-28T13:00:00Z',
  rangeEnd: '2026-06-28T13:20:00Z',
  loopRange: true,
  ingest: {
    ...DEFAULT_INGEST_WINDOW_STATE,
    preset: 'replay_range' as const,
    replayStart: '2026-06-28T13:00:00Z',
    replayEnd: '2026-06-28T13:20:00Z',
  },
};

describe('parseBookmarksStore', () => {
  it('returns empty store for malformed JSON', () => {
    expect(parseBookmarksStore('{not json')).toEqual(emptyBookmarksStore());
  });

  it('returns empty store for wrong schema version', () => {
    expect(parseBookmarksStore(JSON.stringify({ schemaVersion: 99, bookmarks: [] }))).toEqual(
      emptyBookmarksStore(),
    );
  });
});

describe('validateBookmark', () => {
  it('accepts a valid bookmark', () => {
    const bookmark = createBookmarkFromSnapshot('Storm A', sampleSnapshot);
    expect(validateBookmark(bookmark)?.name).toBe('Storm A');
  });

  it('rejects invalid bookmark names', () => {
    expect(validateBookmark({ ...createBookmarkFromSnapshot('Storm A', sampleSnapshot), name: '' })).toBeNull();
  });
});

describe('read/write bookmarks store', () => {
  let storage: MemoryStorage;

  beforeEach(() => {
    storage = new MemoryStorage();
    vi.stubGlobal('localStorage', storage);
  });

  it('round-trips bookmarks through local storage', () => {
    const bookmark = createBookmarkFromSnapshot('Storm A', sampleSnapshot);
    writeBookmarksStore({ ...emptyBookmarksStore(), bookmarks: [bookmark] }, storage);
    const loaded = readBookmarksStore(storage);
    expect(loaded.bookmarks).toHaveLength(1);
    expect(loaded.bookmarks[0].name).toBe('Storm A');
    expect(storage.getItem(REPLAY_BOOKMARKS_STORAGE_KEY)).toBe(
      serializeBookmarksStore({ ...emptyBookmarksStore(), bookmarks: [bookmark] }),
    );
  });
});

describe('buildBookmarkRestorePlan', () => {
  it('restores selected frame when present in timeline', () => {
    const bookmark = createBookmarkFromSnapshot('Storm A', sampleSnapshot);
    const plan = buildBookmarkRestorePlan(bookmark, [
      '2026-06-28T12:50:00Z',
      '2026-06-28T13:00:00Z',
      '2026-06-28T13:20:00Z',
    ]);
    expect(plan.selectedTime).toBe('2026-06-28T13:00:00Z');
    expect(plan.loopRange).toBe(true);
    expect(plan.hints).toEqual([]);
  });

  it('warns when saved timestamps are missing from timeline', () => {
    const bookmark = createBookmarkFromSnapshot('Storm A', sampleSnapshot);
    const plan = buildBookmarkRestorePlan(bookmark, []);
    expect(plan.selectedTime).toBeNull();
    expect(plan.rangeStart).toBe('2026-06-28T13:00:00Z');
    expect(plan.hints.some((hint) => hint.includes('not in the current timeline'))).toBe(true);
  });
});

describe('resolveRestoreSelectedTime', () => {
  it('falls back to range start when selected frame is missing', () => {
    const bookmark = createBookmarkFromSnapshot('Storm A', sampleSnapshot);
    expect(resolveRestoreSelectedTime(bookmark, ['2026-06-28T13:00:00Z'])).toBe(
      '2026-06-28T13:00:00Z',
    );
  });
});
