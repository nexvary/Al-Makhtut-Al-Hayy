export type HistoricalObject = {
  id: string;
  manuscript_id: string;
  name: string;
  category: string;
  description?: string | null;
  region_ids: string[];
  media: Array<{
    id: string;
    kind: "image" | "audio" | "video" | "model_3d" | "animation";
    url: string;
    label?: string | null;
    license?: string | null;
    attribution?: string | null;
  }>;
  warnings: Array<{ code: string; text: string; severity: string }>;
};

export async function loadHistoricalObjects(
  apiBase: string,
  manuscriptId: string,
): Promise<HistoricalObject[]> {
  const base = apiBase.replace(/\/$/, "");
  const url = new URL(`${base}/api/v1/visual/objects`);
  url.searchParams.set("manuscript_id", manuscriptId);
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Visual knowledge request failed: ${response.status}`);
  return (await response.json()) as HistoricalObject[];
}
