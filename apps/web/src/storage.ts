export type Bookmark = {
  source: string;
  pageIndex: number;
  label: string;
  savedAt: string;
};

const KEY = "al-makhtut-al-hayy/bookmarks/v1";

export function getBookmarks(): Bookmark[] {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Bookmark[]) : [];
  } catch {
    return [];
  }
}

export function saveBookmark(bookmark: Bookmark): Bookmark[] {
  const current = getBookmarks().filter(
    (item) => !(item.source === bookmark.source && item.pageIndex === bookmark.pageIndex),
  );
  const next = [bookmark, ...current].slice(0, 100);
  localStorage.setItem(KEY, JSON.stringify(next));
  return next;
}
