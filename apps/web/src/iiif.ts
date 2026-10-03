export type IiifPage = {
  id: string;
  label: string;
  tileSource: string | Record<string, unknown>;
  imageUrl?: string;
};

function labelText(value: unknown, fallback: string): string {
  if (typeof value === "string") return value;
  if (value && typeof value === "object") {
    const obj = value as Record<string, unknown>;
    const candidates = ["ar", "en", "none"];
    for (const key of candidates) {
      const item = obj[key];
      if (Array.isArray(item) && typeof item[0] === "string") return item[0];
    }
    for (const item of Object.values(obj)) {
      if (Array.isArray(item) && typeof item[0] === "string") return item[0];
    }
    if (typeof obj["@value"] === "string") return obj["@value"];
  }
  return fallback;
}

function serviceId(service: unknown): string | undefined {
  if (!service) return undefined;
  const first = Array.isArray(service) ? service[0] : service;
  if (!first || typeof first !== "object") return undefined;
  const obj = first as Record<string, unknown>;
  const id = obj.id ?? obj["@id"];
  return typeof id === "string" ? id.replace(/\/$/, "") : undefined;
}

export async function loadIiifManifest(url: string): Promise<IiifPage[]> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`IIIF manifest request failed: ${response.status}`);
  const manifest = await response.json() as Record<string, any>;

  // IIIF Presentation API v3
  if (Array.isArray(manifest.items)) {
    return manifest.items.map((canvas: any, index: number) => {
      const annotationPage = canvas.items?.[0];
      const annotation = annotationPage?.items?.[0];
      const body = annotation?.body;
      const sid = serviceId(body?.service);
      const imageUrl = typeof body?.id === "string" ? body.id : undefined;
      if (!sid && !imageUrl) throw new Error(`Canvas ${index + 1} has no usable image source`);
      return {
        id: String(canvas.id ?? `canvas-${index + 1}`),
        label: labelText(canvas.label, `صفحة ${index + 1}`),
        tileSource: sid ? `${sid}/info.json` : { type: "image", url: imageUrl! },
        imageUrl
      };
    });
  }

  // IIIF Presentation API v2
  const canvases = manifest.sequences?.[0]?.canvases;
  if (Array.isArray(canvases)) {
    return canvases.map((canvas: any, index: number) => {
      const resource = canvas.images?.[0]?.resource;
      const sid = serviceId(resource?.service);
      const imageUrl = typeof resource?.["@id"] === "string" ? resource["@id"] : undefined;
      if (!sid && !imageUrl) throw new Error(`Canvas ${index + 1} has no usable image source`);
      return {
        id: String(canvas["@id"] ?? `canvas-${index + 1}`),
        label: labelText(canvas.label, `صفحة ${index + 1}`),
        tileSource: sid ? `${sid}/info.json` : { type: "image", url: imageUrl! },
        imageUrl
      };
    });
  }

  throw new Error("Unsupported IIIF manifest: no canvases/items found.");
}
