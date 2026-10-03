import type { Manuscript } from "./types";

export function downloadOfflineMetadata(manuscript: Manuscript): void {
  const payload = {
    format: "al-makhtut-offline-pack/v1",
    createdAt: new Date().toISOString(),
    includesImages: false,
    sourceNotice:
      "Images are excluded. Cache or redistribute source images only when source rights permit.",
    manuscript,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${manuscript.id}.offline.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}
