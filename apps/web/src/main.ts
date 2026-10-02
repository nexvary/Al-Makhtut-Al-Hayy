import OpenSeadragon from "openseadragon";
import { loadIiifManifest, type IiifPage } from "./iiif";
import "./styles.css";

const DEFAULT_MANIFEST =
  "https://gallica.bnf.fr/iiif/ark:/12148/btv1b84061750/manifest.json";

type DemoRegion = {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  htr: string;
  verified: string;
  normalized: string;
  confidence: number;
};

const demoRegions: DemoRegion[] = [
  {
    id: "demo-line-1",
    x: 0.18,
    y: 0.28,
    width: 0.64,
    height: 0.055,
    htr: "نص آلي تجريبي — سيستبدل بخروج Kraken",
    verified: "هذه طبقة مراجعة بشرية تجريبية.",
    normalized: "هذه صياغة حديثة تجريبية مرتبطة بنفس موضع السطر.",
    confidence: 0.72
  },
  {
    id: "demo-line-2",
    x: 0.2,
    y: 0.35,
    width: 0.58,
    height: 0.055,
    htr: "منطقة ثانية لاختبار التحديد المتزامن",
    verified: "يمكن للمحقق تعديل هذا النص دون تغيير طبقة HTR الأصلية.",
    normalized: "يظل كل نص مرتبطًا بإحداثياته ومصدره.",
    confidence: 0.81
  }
];

document.querySelector<HTMLDivElement>("#app")!.innerHTML = `
  <main class="shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Living Manuscript</p>
        <h1>المخطوط الحي</h1>
      </div>
      <div class="source-badge">IIIF • مصدر خارجي</div>
    </header>

    <section class="source-panel">
      <label for="manifest">رابط IIIF Manifest</label>
      <div class="source-row">
        <input id="manifest" value="${DEFAULT_MANIFEST}" spellcheck="false" />
        <button id="load">فتح المخطوط</button>
      </div>
      <p id="status">جاهز لفتح مخطوط الزهراوي من Gallica.</p>
    </section>

    <section class="workspace">
      <div class="viewer-column">
        <div class="viewer-toolbar">
          <button id="prev" aria-label="الصفحة السابقة">→ السابق</button>
          <strong id="pageLabel">—</strong>
          <span id="pageCount">—</span>
          <button id="next" aria-label="الصفحة التالية">التالي ←</button>
        </div>
        <div id="viewer"></div>
      </div>

      <aside class="text-panel">
        <div class="panel-heading">
          <span class="dot"></span>
          <h2>النص المرتبط بالصفحة</h2>
        </div>
        <p class="hint">اضغط على إطار فوق المخطوط، أو على بطاقة النص. الإطارات الحالية تجريبية حتى توصيل Kraken.</p>
        <div id="regions"></div>
      </aside>
    </section>

    <footer>
      النموذج لا ينسخ صور Gallica داخل المشروع؛ يتم عرضها من المصدر عبر IIIF.
    </footer>
  </main>
`;

const manifestInput = document.querySelector<HTMLInputElement>("#manifest")!;
const loadButton = document.querySelector<HTMLButtonElement>("#load")!;
const status = document.querySelector<HTMLParagraphElement>("#status")!;
const pageLabel = document.querySelector<HTMLElement>("#pageLabel")!;
const pageCount = document.querySelector<HTMLElement>("#pageCount")!;
const prevButton = document.querySelector<HTMLButtonElement>("#prev")!;
const nextButton = document.querySelector<HTMLButtonElement>("#next")!;
const regionsRoot = document.querySelector<HTMLDivElement>("#regions")!;

let pages: IiifPage[] = [];
let pageIndex = 0;
let overlayElements = new Map<string, HTMLElement>();

const viewer = OpenSeadragon({
  id: "viewer",
  prefixUrl: "https://cdnjs.cloudflare.com/ajax/libs/openseadragon/5.0.1/images/",
  showNavigator: true,
  showRotationControl: true,
  gestureSettingsMouse: { clickToZoom: false }
});

function setStatus(message: string, error = false) {
  status.textContent = message;
  status.classList.toggle("error", error);
}

function selectRegion(id: string) {
  overlayElements.forEach((el, key) => el.classList.toggle("selected", key === id));
  document.querySelectorAll<HTMLElement>(".region-card").forEach((card) => {
    card.classList.toggle("selected", card.dataset.regionId === id);
  });
}

function renderRegionCards() {
  regionsRoot.innerHTML = demoRegions.map((region) => `
    <article class="region-card" data-region-id="${region.id}" tabindex="0">
      <div class="region-meta">
        <span>HTR ${Math.round(region.confidence * 100)}%</span>
        <span class="machine">آلي</span>
      </div>
      <h3>التفريغ الآلي</h3>
      <p>${region.htr}</p>
      <h3>النص المراجع</h3>
      <p>${region.verified}</p>
      <h3>العربية الحديثة</h3>
      <p>${region.normalized}</p>
    </article>
  `).join("");

  document.querySelectorAll<HTMLElement>(".region-card").forEach((card) => {
    const activate = () => selectRegion(card.dataset.regionId!);
    card.addEventListener("click", activate);
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") activate();
    });
  });
}

function addDemoOverlays() {
  viewer.clearOverlays();
  overlayElements = new Map();

  const item = viewer.world.getItemAt(0);
  if (!item) return;
  const size = item.getContentSize();

  for (const region of demoRegions) {
    const element = document.createElement("button");
    element.className = "manuscript-region";
    element.title = "منطقة نص مرتبطة";
    element.addEventListener("click", (event) => {
      event.stopPropagation();
      selectRegion(region.id);
    });

    const imageRect = new OpenSeadragon.Rect(
      region.x * size.x,
      region.y * size.y,
      region.width * size.x,
      region.height * size.y
    );
    const viewportRect = item.imageToViewportRectangle(imageRect);
    viewer.addOverlay({ element, location: viewportRect });
    overlayElements.set(region.id, element);
  }
}

function openPage(index: number) {
  if (!pages.length) return;
  pageIndex = Math.max(0, Math.min(index, pages.length - 1));
  const page = pages[pageIndex];

  pageLabel.textContent = page.label;
  pageCount.textContent = `${pageIndex + 1} / ${pages.length}`;
  prevButton.disabled = pageIndex === 0;
  nextButton.disabled = pageIndex === pages.length - 1;
  viewer.open(page.tileSource as any);
}

viewer.addHandler("open", () => {
  addDemoOverlays();
  setStatus("تم فتح الصفحة. مناطق النص الحالية Prototype لحين ربط HTR.");
});

viewer.addHandler("open-failed", (event: any) => {
  setStatus(`تعذر فتح الصورة: ${event?.message ?? "خطأ غير معروف"}`, true);
});

async function loadManifest() {
  loadButton.disabled = true;
  setStatus("جارٍ قراءة IIIF Manifest…");
  try {
    pages = await loadIiifManifest(manifestInput.value.trim());
    if (!pages.length) throw new Error("المخطوط لا يحتوي صفحات قابلة للعرض.");
    openPage(0);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    setStatus(`تعذر تحميل المخطوط: ${message}`, true);
  } finally {
    loadButton.disabled = false;
  }
}

loadButton.addEventListener("click", loadManifest);
prevButton.addEventListener("click", () => openPage(pageIndex - 1));
nextButton.addEventListener("click", () => openPage(pageIndex + 1));

renderRegionCards();
void loadManifest();
