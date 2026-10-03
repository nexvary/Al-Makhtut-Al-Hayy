import type { Manuscript } from "./types";

export async function loadManuscript(apiBase: string, manuscriptId: string): Promise<Manuscript> {
  const base = apiBase.replace(/\/$/, "");
  const response = await fetch(`${base}/api/v1/manuscripts/${encodeURIComponent(manuscriptId)}`);
  if (!response.ok) {
    throw new Error(`API manuscript request failed: ${response.status}`);
  }
  return (await response.json()) as Manuscript;
}
