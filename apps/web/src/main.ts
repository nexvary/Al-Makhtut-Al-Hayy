import { AccountsPanel } from "./accounts";
import { VisualSearchPanel } from "./visual-search";
import { MuseumPanel } from "./museum";
import { HeritagePanel } from "./heritage";
import { AcademyPanel } from "./academy";
import { OttomanPanel } from "./ottoman";
import { LivingLayersPanel } from "./layers";
import OpenSeadragon from "openseadragon";
import { loadManuscript } from "./api";
import { loadIiifManifest, type IiifPage } from "./iiif";
import { downloadOfflineMetadata } from "./offline";
import { saveBookmark } from "./storage";
import { speakArabic } from "./tts";
import type { Manuscript, ReadingMode, Region, TextLayer } from "./types";
import "./styles.css";

const DEFAULT_MANIFEST =
  "https://gallica.bnf.fr/iiif/ark:/12148/btv1b84061750/manifest.json";

document.querySelector<HTMLDivElement>("#app")!.innerHTML = `
  <main class="shell">
    <header class="topbar">
      <div><p class="eyebrow">Living Manuscript</p><h1>المخطوط الحي</h1></div>
      <div class="source-badge">IIIF • مصدر موثّق</div>
    </header>

    <section class="source-panel">
      <label for="manifest">رابط IIIF Manifest</label>
      <div class="source-row">
        <input id="manifest" value="${DEFAULT_MANIFEST}" spellcheck="false" />
        <button id="load">فتح المخطوط</button>
      </div>
      <details>
        <summary>ربط طبقات النص من API</summary>
        <div class="source-row api-row">
          <input id="apiBase" value="http://localhost:8000" aria-label="عنوان API" />
          <input id="manuscriptId" placeholder="معرّف المخطوط" aria-label="معرّف المخطوط" />
          <button id="loadApi">تحميل النص</button>
        </div>
      </details>
      <p id="status">جاهز لفتح مخطوط الزهراوي من Gallica.</p>
    </section>

    <section class="workspace">
      <div class="viewer-column">
        <div class="viewer-toolbar">
          <button id="prev">→ السابق</button>
          <strong id="pageLabel">—</strong><span id="pageCount">—</span>
          <button id="next">التالي ←</button>
          <button id="bookmark">☆ حفظ</button>
        </div>
        <div id="viewer" tabindex="0" aria-label="عارض المخطوط"></div>
      </div>

      <aside class="text-panel">
        <div class="panel-heading"><span class="dot"></span><h2>النص المرتبط بالصفحة</h2></div>
        <div class="reader-controls">
          <label>وضع القراءة
            <select id="readingMode">
              <option value="general">قارئ عام</option>
              <option value="student">طالب</option>
              <option value="researcher">باحث</option>
            </select>
          </label>
          <button id="speak" disabled>🔊 استمع</button>
          <button id="offline" disabled>حزمة Offline</button>
        </div>
        <p class="hint" id="regionHint">لا توجد طبقات نص محمّلة. اربط مخطوطًا من API لعرض HTR والنص المراجع.</p>
        <div id="regions"></div>
        <details id="livingLayers"></details>
        <details id="ottomanLab"></details>
        <details id="ottomanAcademy"></details>
        <details id="heritageGraph"></details>
        <details id="livingMuseum"></details>
        <details id="visualSearch"></details>
        <details id="accounts"></details>
      </aside>
    </section>

    <footer>صور المؤسسات الخارجية لا تُضمّن في حزمة Offline افتراضيًا.</footer>
  </main>
`;

const manifestInput = document.querySelector<HTMLInputElement>("#manifest")!;
const apiBaseInput = document.querySelector<HTMLInputElement>("#apiBase")!;
const manuscriptIdInput = document.querySelector<HTMLInputElement>("#manuscriptId")!;
const status = document.querySelector<HTMLParagraphElement>("#status")!;
const pageLabel = document.querySelector<HTMLElement>("#pageLabel")!;
const pageCount = document.querySelector<HTMLElement>("#pageCount")!;
const regionsRoot = document.querySelector<HTMLDivElement>("#regions")!;
const hint = document.querySelector<HTMLElement>("#regionHint")!;
const modeSelect = document.querySelector<HTMLSelectElement>("#readingMode")!;
const speakButton = document.querySelector<HTMLButtonElement>("#speak")!;
const offlineButton = document.querySelector<HTMLButtonElement>("#offline")!;

let pages: IiifPage[] = [];
let pageIndex = 0;
let manuscript: Manuscript | null = null;
let selectedRegion: Region | null = null;
let sourceRequest = 0;
let pendingRegionId: string | null = null;
let overlayElements = new Map<string, HTMLElement>();
let readingMode: ReadingMode = "general";
const livingLayers = new LivingLayersPanel(document.querySelector<HTMLElement>("#livingLayers")!, () => ({
  base: apiBaseInput.value.trim(), manuscript, page: currentApiPage(), region: selectedRegion,
}));

const ottomanLab = new OttomanPanel(document.querySelector<HTMLElement>("#ottomanLab")!, () => ({
  base: apiBaseInput.value.trim(), manuscript, page: currentApiPage(), region: selectedRegion,
}));

const ottomanAcademy = new AcademyPanel(document.querySelector<HTMLElement>("#ottomanAcademy")!, () => ({
  base: apiBaseInput.value.trim(), manuscript, page: currentApiPage(),
}));

new AccountsPanel(document.querySelector<HTMLElement>("#accounts")!, () => apiBaseInput.value.trim());

new HeritagePanel(document.querySelector<HTMLElement>("#heritageGraph")!, () => apiBaseInput.value.trim());

new MuseumPanel(document.querySelector<HTMLElement>("#livingMuseum")!, () => apiBaseInput.value.trim());
new VisualSearchPanel(document.querySelector<HTMLElement>("#visualSearch")!, () => ({base:apiBaseInput.value.trim(),manuscript,page:currentApiPage(),region:selectedRegion}), async source => {
  manuscriptIdInput.value = source.manuscript_id;
  await loadApiLayers(source.page_id, source.region_id);
});

const viewer = OpenSeadragon({
  id: "viewer",
  prefixUrl: "https://cdnjs.cloudflare.com/ajax/libs/openseadragon/5.0.1/images/",
  showNavigator: true,
  showRotationControl: true,
  gestureSettingsMouse: { clickToZoom: false },
});

function setStatus(message: string, error = false) {
  status.textContent = message;
  status.classList.toggle("error", error);
}

function currentApiPage() {
  if (!manuscript) return null;
  const iiif = pages[pageIndex];
  return (
    manuscript.pages.find((page) => page.id === iiif?.id || page.canvas_uri === iiif?.id) ??
    manuscript.pages.find((page) => page.sequence === pageIndex + 1) ??
    null
  );
}

function layersForMode(layers: TextLayer[]): TextLayer[] {
  if (readingMode === "researcher") return layers;
  const allowed =
    readingMode === "student"
      ? new Set(["verified_transcription", "normalized_arabic", "simplified_arabic", "ai_explanation"])
      : new Set(["verified_transcription", "normalized_arabic", "simplified_arabic"]);
  const filtered = layers.filter((layer) => allowed.has(layer.kind));
  return filtered.length ? filtered : layers.slice(0, 1);
}

function selectRegion(region: Region | null) {
  selectedRegion = region;
  overlayElements.forEach((element, id) => element.classList.toggle("selected", id === region?.id));
  document.querySelectorAll<HTMLElement>(".region-card").forEach((card) => {
    card.classList.toggle("selected", card.dataset.regionId === region?.id);
  });
  speakButton.disabled = !region;
  void livingLayers.refresh();
  void ottomanLab.refresh();
  void ottomanAcademy.refresh();
}

function bestSpeechText(region: Region): string {
  const priority = ["simplified_arabic", "normalized_arabic", "verified_transcription", "htr_raw"];
  for (const kind of priority) {
    const layer = region.layers.find((item) => item.kind === kind);
    if (layer?.text) return layer.text;
  }
  return region.layers[0]?.text ?? "";
}

function renderRegionCards(regions: Region[]) {
  regionsRoot.replaceChildren();
  hint.hidden = regions.length > 0;
  for (const region of regions) {
    const card = document.createElement("article");
    card.className = "region-card";
    card.tabIndex = 0;
    card.dataset.regionId = region.id;

    const meta = document.createElement("div");
    meta.className = "region-meta";
    meta.textContent = region.region_type ?? "text_line";
    card.append(meta);

    for (const layer of layersForMode(region.layers)) {
      const title = document.createElement("h3");
      title.textContent = layer.kind.replaceAll("_", " ");
      const badge = document.createElement("span");
      badge.className = `status-chip ${layer.status}`;
      badge.textContent = layer.status === "verified" ? "موثّق" : layer.status === "draft" ? "مسودة" : "آلي";
      title.append(" ", badge);

      const paragraph = document.createElement("p");
      paragraph.textContent = layer.text;
      card.append(title, paragraph);
    }

    const activate = () => selectRegion(region);
    card.addEventListener("click", activate);
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        activate();
      }
    });
    regionsRoot.append(card);
  }
}

function addRegionOverlays(regions: Region[]) {
  viewer.clearOverlays();
  overlayElements.clear();
  const item = viewer.world.getItemAt(0);
  if (!item) return;

  for (const region of regions) {
    if (region.polygon.length < 2) continue;
    const xs = region.polygon.map((point) => point.x);
    const ys = region.polygon.map((point) => point.y);
    const left = Math.min(...xs);
    const top = Math.min(...ys);
    const imageRect = new OpenSeadragon.Rect(
      left,
      top,
      Math.max(...xs) - left,
      Math.max(...ys) - top,
    );
    const element = document.createElement("button");
    element.className = "manuscript-region";
    element.ariaLabel = "منطقة نص";
    element.addEventListener("click", (event) => {
      event.stopPropagation();
      selectRegion(region);
    });
    viewer.addOverlay({ element, location: item.imageToViewportRectangle(imageRect) });
    overlayElements.set(region.id, element);
  }
}

function refreshTextLayer() {
  const regions = currentApiPage()?.regions ?? [];
  renderRegionCards(regions);
  if (viewer.world.getItemCount()) addRegionOverlays(regions);
  selectRegion(regions.find(region => region.id === pendingRegionId) ?? null);
}

function openPage(index: number) {
  if (!pages.length) return;
  pageIndex = Math.max(0, Math.min(index, pages.length - 1));
  const page = pages[pageIndex];
  pageLabel.textContent = page.label;
  pageCount.textContent = `${pageIndex + 1} / ${pages.length}`;
  document.querySelector<HTMLButtonElement>("#prev")!.disabled = pageIndex === 0;
  document.querySelector<HTMLButtonElement>("#next")!.disabled = pageIndex === pages.length - 1;
  viewer.open(page.tileSource as unknown as OpenSeadragon.TileSource);
}

viewer.addHandler("open", () => {
  refreshTextLayer();
  pendingRegionId = null;
  setStatus(manuscript ? `تم ربط ${manuscript.title} بطبقات النص وفتح الصفحة الأصلية.` : "تم فتح الصفحة من IIIF.");
});
viewer.addHandler("open-failed", (event: OpenSeadragon.OpenFailedEvent) => {
  setStatus(`تعذر فتح الصورة: ${event.message ?? "خطأ غير معروف"}`, true);
});

async function loadManifest() {
  const ticket = ++sourceRequest;
  setStatus("جارٍ قراءة IIIF Manifest…");
  try {
    const loaded = await loadIiifManifest(manifestInput.value.trim());
    if (ticket !== sourceRequest) return;
    pages = loaded;
    pendingRegionId = null;
    if (!pages.length) throw new Error("المخطوط لا يحتوي صفحات قابلة للعرض.");
    manuscript = null;
    offlineButton.disabled = true;
    openPage(0);
  } catch (error) {
    if (ticket !== sourceRequest) return;
    setStatus(`تعذر تحميل المخطوط: ${error instanceof Error ? error.message : String(error)}`, true);
  }
}

async function loadApiLayers(pageId?: string, regionId: string | null = null) {
  const ticket = ++sourceRequest;
  try {
    const loaded = await loadManuscript(apiBaseInput.value.trim(), manuscriptIdInput.value.trim());
    if (ticket !== sourceRequest) return;
    const ordered = [...loaded.pages].sort((left, right) => left.sequence - right.sequence);
    if (!ordered.length) throw new Error("المخطوط لا يحتوي صفحات قابلة للعرض.");
    const index = pageId ? ordered.findIndex(page => page.id === pageId) : 0;
    if (index < 0) throw new Error("صفحة الدليل غير موجودة في هذا المخطوط.");
    if (regionId && !ordered[index].regions.some(region => region.id === regionId)) {
      throw new Error("منطقة الدليل غير موجودة في هذه الصفحة.");
    }
    manuscript = loaded;
    pages = ordered.map(page => ({id: page.id, label: page.folio_label || `صفحة ${page.sequence}`,
      imageUrl: page.image, tileSource: {type: "image", url: page.image}}));
    pendingRegionId = regionId;
    offlineButton.disabled = false;
    // Clear old text immediately; only the selected source page can supply overlays.
    regionsRoot.replaceChildren(); viewer.clearOverlays(); overlayElements.clear();
    selectedRegion = null; speakButton.disabled = true;
    openPage(index);
    refreshTextLayer();
    setStatus(`تم ربط ${manuscript.title} بطبقات النص.`);
  } catch (error) {
    if (ticket !== sourceRequest) return;
    setStatus(`تعذر ربط API: ${error instanceof Error ? error.message : String(error)}`, true);
  }
}

document.querySelector<HTMLButtonElement>("#load")!.addEventListener("click", () => void loadManifest());
document.querySelector<HTMLButtonElement>("#loadApi")!.addEventListener("click", () => void loadApiLayers());
document.querySelector<HTMLButtonElement>("#prev")!.addEventListener("click", () => { pendingRegionId = null; openPage(pageIndex - 1); });
document.querySelector<HTMLButtonElement>("#next")!.addEventListener("click", () => { pendingRegionId = null; openPage(pageIndex + 1); });
document.querySelector<HTMLButtonElement>("#bookmark")!.addEventListener("click", () => {
  saveBookmark({
    source: manifestInput.value.trim(),
    pageIndex,
    label: pageLabel.textContent ?? `صفحة ${pageIndex + 1}`,
    savedAt: new Date().toISOString(),
  });
  setStatus("تم حفظ موضع القراءة على هذا الجهاز.");
});
modeSelect.addEventListener("change", () => {
  readingMode = modeSelect.value as ReadingMode;
  livingLayers.setMode(readingMode);
  refreshTextLayer();
});
speakButton.addEventListener("click", () => {
  if (!selectedRegion) return;
  const text = bestSpeechText(selectedRegion);
  if (!text) return;
  try {
    speakArabic(text);
  } catch (error) {
    setStatus(error instanceof Error ? error.message : String(error), true);
  }
});
offlineButton.addEventListener("click", () => {
  if (manuscript) downloadOfflineMetadata(manuscript);
});
window.addEventListener("keydown", (event) => {
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLSelectElement) return;
  if (event.key === "ArrowRight") openPage(pageIndex - 1);
  if (event.key === "ArrowLeft") openPage(pageIndex + 1);
  if (event.key === "Escape") selectRegion(null);
});

void loadManifest();
