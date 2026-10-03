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
let overlayElements = new Map<string, HTMLElement>();
let readingMode: ReadingMode = "general";

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
    manuscript.pages.find((page) => page.canvas_uri === iiif?.id) ??
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
  selectRegion(null);
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
  setStatus(manuscript ? "تم فتح الصفحة وربط طبقات النص من API." : "تم فتح الصفحة من IIIF.");
});
viewer.addHandler("open-failed", (event: OpenSeadragon.OpenFailedEvent) => {
  setStatus(`تعذر فتح الصورة: ${event.message ?? "خطأ غير معروف"}`, true);
});

async function loadManifest() {
  setStatus("جارٍ قراءة IIIF Manifest…");
  try {
    pages = await loadIiifManifest(manifestInput.value.trim());
    if (!pages.length) throw new Error("المخطوط لا يحتوي صفحات قابلة للعرض.");
    manuscript = null;
    offlineButton.disabled = true;
    openPage(0);
  } catch (error) {
    setStatus(`تعذر تحميل المخطوط: ${error instanceof Error ? error.message : String(error)}`, true);
  }
}

async function loadApiLayers() {
  try {
    manuscript = await loadManuscript(apiBaseInput.value.trim(), manuscriptIdInput.value.trim());
    offlineButton.disabled = false;
    refreshTextLayer();
    setStatus(`تم ربط ${manuscript.title} بطبقات النص.`);
  } catch (error) {
    setStatus(`تعذر ربط API: ${error instanceof Error ? error.message : String(error)}`, true);
  }
}

document.querySelector<HTMLButtonElement>("#load")!.addEventListener("click", () => void loadManifest());
document.querySelector<HTMLButtonElement>("#loadApi")!.addEventListener("click", () => void loadApiLayers());
document.querySelector<HTMLButtonElement>("#prev")!.addEventListener("click", () => openPage(pageIndex - 1));
document.querySelector<HTMLButtonElement>("#next")!.addEventListener("click", () => openPage(pageIndex + 1));
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
