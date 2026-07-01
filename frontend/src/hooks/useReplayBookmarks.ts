import { useCallback, useEffect, useState } from 'react';
import {
  buildBookmarkRestorePlan,
  createBookmarkFromSnapshot,
  emptyBookmarksStore,
  MAX_REPLAY_BOOKMARKS,
  readBookmarksStore,
  type BookmarkRestorePlan,
  type ReplayBookmark,
  type ReplayBookmarkSnapshot,
  writeBookmarksStore,
} from './replayBookmarks';

export function useReplayBookmarks() {
  const [bookmarks, setBookmarks] = useState<ReplayBookmark[]>([]);
  const [storageWarning, setStorageWarning] = useState<string | null>(null);
  const [lastLoadedId, setLastLoadedId] = useState<string | null>(null);
  const [restoreHints, setRestoreHints] = useState<string[]>([]);

  useEffect(() => {
    const store = readBookmarksStore();
    setBookmarks(store.bookmarks);
  }, []);

  const persist = useCallback((nextBookmarks: ReplayBookmark[]) => {
    if (nextBookmarks.length > MAX_REPLAY_BOOKMARKS) {
      setStorageWarning(`Only the first ${MAX_REPLAY_BOOKMARKS} bookmarks are kept.`);
    } else {
      setStorageWarning(null);
    }
    const store = writeBookmarksStore({ ...emptyBookmarksStore(), bookmarks: nextBookmarks });
    setBookmarks(store.bookmarks);
    return store.bookmarks;
  }, []);

  const saveBookmark = useCallback(
    (name: string, snapshot: ReplayBookmarkSnapshot) => {
      const trimmed = name.trim();
      if (!trimmed) {
        return null;
      }
      const bookmark = createBookmarkFromSnapshot(trimmed, snapshot);
      const next = [bookmark, ...bookmarks.filter((item) => item.name !== trimmed)].slice(
        0,
        MAX_REPLAY_BOOKMARKS,
      );
      persist(next);
      setLastLoadedId(bookmark.id);
      setRestoreHints([]);
      return bookmark;
    },
    [bookmarks, persist],
  );

  const deleteBookmark = useCallback(
    (id: string) => {
      const next = bookmarks.filter((bookmark) => bookmark.id !== id);
      persist(next);
      if (lastLoadedId === id) {
        setLastLoadedId(null);
        setRestoreHints([]);
      }
    },
    [bookmarks, lastLoadedId, persist],
  );

  const renameBookmark = useCallback(
    (id: string, name: string) => {
      const trimmed = name.trim();
      if (!trimmed) {
        return null;
      }
      const now = new Date().toISOString().replace('.000Z', 'Z');
      const next = bookmarks.map((bookmark) =>
        bookmark.id === id ? { ...bookmark, name: trimmed, updatedAt: now } : bookmark,
      );
      persist(next);
      return next.find((bookmark) => bookmark.id === id) ?? null;
    },
    [bookmarks, persist],
  );

  const planBookmarkRestore = useCallback(
    (id: string, playbackTimes: string[]): BookmarkRestorePlan | null => {
      const bookmark = bookmarks.find((item) => item.id === id);
      if (!bookmark) {
        return null;
      }
      const plan = buildBookmarkRestorePlan(bookmark, playbackTimes);
      setLastLoadedId(id);
      setRestoreHints(plan.hints);
      return plan;
    },
    [bookmarks],
  );

  const clearRestoreHints = useCallback(() => {
    setRestoreHints([]);
  }, []);

  return {
    bookmarks,
    storageWarning,
    lastLoadedId,
    restoreHints,
    saveBookmark,
    deleteBookmark,
    renameBookmark,
    planBookmarkRestore,
    clearRestoreHints,
  };
}

export type ReplayBookmarksState = ReturnType<typeof useReplayBookmarks>;
