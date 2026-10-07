export type TextLayerKind =
  | "htr_raw"
  | "diplomatic_transcription"
  | "verified_transcription"
  | "normalized_arabic"
  | "simplified_arabic"
  | "translation"
  | "ai_explanation";

export type TextLayer = {
  kind: TextLayerKind;
  text: string;
  status: "machine" | "draft" | "verified";
  confidence?: number | null;
  model?: string | null;
  revision?: string | null;
};

export type Point = { x: number; y: number };

export type Region = {
  id: string;
  region_type?: string;
  reading_order?: number | null;
  polygon: Point[];
  layers: TextLayer[];
};

export type ManuscriptPage = {
  id: string;
  sequence: number;
  folio_label?: string | null;
  image: string;
  canvas_uri?: string | null;
  regions: Region[];
};

export type Manuscript = {
  id: string;
  title: string;
  author?: string | null;
  source_url?: string | null;
  license?: string | null;
  pages: ManuscriptPage[];
};

export type ReadingMode = "general" | "student" | "researcher";
