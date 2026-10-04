import type { Manuscript, ManuscriptPage, Region } from "./types";
type Context = { base: string; manuscript: Manuscript | null; page: ManuscriptPage | null; region: Region | null };
type Layer = { id: string; kind: string; state: string; language: string | null; text: string | null;
  provenance: { confidence: number | null; reviewer: string | null; timestamp: string; source: { region_id: string | null } } };

const layerLabels: Record<string, string> = {
  original_image: "الأصل", machine_reading: "قراءة آلية", draft_transcription: "مسودة",
  verified_transcription: "تحقيق", critical_text: "نص نقدي", modernized_text: "لغة حديثة",
  simplified_explanation: "شرح", translation: "ترجمة", audio: "صوت", named_entities: "أعلام",
  historical_objects: "أدوات تاريخية", illustrations: "رسومات", references: "مراجع",
  annotations: "تعليقات", provenance: "توثيق",
};
export class LivingLayersPanel {
  private layers: Layer[] = [];
  private version = 0;
  private mode = "general";
  constructor(private root: HTMLElement, private context: () => Context) {
    root.innerHTML = `<summary>طبقات المخطوط وسجل المراجعة</summary>
      <p>الأصل محفوظ دائمًا. القراءة الآلية والمسودة والتحقيق طبقات منفصلة.</p>
      <button type="button" data-refresh>تحديث الطبقات</button><p role="status" data-status></p><div data-layers></div>
      <form data-editor hidden>
        <label>رمز دخول المحرر <input data-token type="password" autocomplete="off" /></label>
        <label>نوع النص <select data-kind>
          <option value="draft_transcription">مسودة قراءة</option><option value="critical_text">نص نقدي</option>
          <option value="modernized_text">لغة حديثة</option><option value="simplified_explanation">شرح مبسط</option>
          <option value="translation">ترجمة</option></select></label>
        <label>لغة النص <input data-language value="ar" maxlength="35" /></label>
        <label>النص <textarea data-text rows="5" maxlength="100000" required></textarea></label>
        <label>هوية المراجع للاعتماد <input data-reviewer autocomplete="off" /></label>
        <button type="submit">حفظ مسودة جديدة</button><button type="button" data-verify>اعتماد بعد المراجعة البشرية</button>
        <p>الاعتماد يحتاج صلاحية مراجع وهوية تطابق حسابه. الكلمات غير المقروءة تبقى غير مؤكدة.</p>
      </form>`;
    root.querySelector("[data-refresh]")!.addEventListener("click", () => void this.refresh());
    root.querySelector("form")!.addEventListener("submit", event => { event.preventDefault(); void this.save(false); });
    root.querySelector("[data-verify]")!.addEventListener("click", () => void this.save(true));
  }
  private input(name: string) { return this.root.querySelector<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(`[data-${name}]`)!; }
  private message(value: string) { this.root.querySelector<HTMLElement>("[data-status]")!.textContent = value; }
  setMode(mode: string) { this.mode = mode; this.root.querySelector<HTMLFormElement>("form")!.hidden = mode !== "researcher"; }
  async refresh() {
    const ticket = ++this.version, context = this.context();
    const list = this.root.querySelector<HTMLElement>("[data-layers]")!;
    list.replaceChildren(); this.layers = [];
    this.root.querySelector<HTMLFormElement>("form")!.hidden = this.mode !== "researcher" || !context.page;
    if (!context.manuscript || !context.page) { this.message("اربط مخطوطًا من الخادم لعرض طبقات موثقة. القارئ الأصلي يعمل مستقلًا."); return; }
    this.message("جارٍ تحميل سجل الطبقات…");
    try {
      const url = `${context.base.replace(/\/$/, "")}/api/v1/living/manuscripts/${encodeURIComponent(context.manuscript.id)}/pages/${encodeURIComponent(context.page.id)}/layers`;
      const response = await fetch(url);
      if (!response.ok) throw new Error(`تعذر تحميل الطبقات (${response.status})`);
      const result = await response.json() as { layers: Layer[] };
      if (ticket !== this.version) return;
      this.layers = result.layers;
      this.message(this.layers.length ? `${this.layers.length} مراجعة محفوظة` : "لا توجد طبقات جديدة لهذه الصفحة.");
      for (const layer of this.layers) {
        if (context.region && layer.provenance.source.region_id !== context.region.id) continue;
        const article = document.createElement("article"); article.className = "region-card";
        const heading = document.createElement("h3"), paragraph = document.createElement("p"), meta = document.createElement("small");
        heading.textContent = `${layerLabels[layer.kind] ?? "طبقة معرفية"} • ${layer.state === "verified" ? "محقق" : layer.state === "machine" ? "آلي" : "مسودة"}`;
        paragraph.textContent = layer.text ?? "مادة مرتبطة بالمصدر";
        meta.textContent = `الثقة: ${layer.provenance.confidence === null ? "غير معروفة" : layer.provenance.confidence} • المراجع: ${layer.provenance.reviewer ?? "لم يُراجع"} • ${layer.provenance.timestamp}`;
        article.append(heading, paragraph, meta); list.append(article);
      }
    } catch (error) { if (ticket === this.version) this.message(String(error)); }
  }
  private async save(verify: boolean) {
    const context = this.context(), token = this.input("token").value.trim(), text = this.input("text").value;
    const reviewer = this.input("reviewer").value.trim();
    if (!context.manuscript || !context.page || !text.trim() || !token) { this.message("اختر صفحة، وأدخل نصًا ورمز دخول صالحًا."); return; }
    if (verify && !reviewer) { this.message("أدخل هوية المراجع للاعتماد."); return; }
    const selected = this.input("kind").value, kind = verify && selected === "draft_transcription" ? "verified_transcription" : selected;
    const language = this.input("language").value.trim() || null, region = context.region?.id ?? null;
    const previous = this.layers.filter(layer => layer.kind === kind && layer.language === language && layer.provenance.source.region_id === region).at(-1);
    const body = { kind, state: verify ? "verified" : "draft", language, text, parent_revision_id: previous?.id ?? null,
      provenance: { source: { manuscript_id: context.manuscript.id, page_id: context.page.id, region_id: region,
        coordinates: context.region?.polygon ?? [], source_uri: context.page.canvas_uri ?? context.page.image },
        extraction_method: "manual", reviewer: verify ? reviewer : null,
        source_text: context.region?.layers.find(layer => layer.status === "verified")?.text ?? null,
        evidence: [{ manuscript_id: context.manuscript.id, page_id: context.page.id, region_id: region }] } };
    const buttons = this.root.querySelectorAll<HTMLButtonElement>("form button"); buttons.forEach(button => button.disabled = true);
    try {
      const response = await fetch(`${context.base.replace(/\/$/, "")}/api/v1/living/layers`, { method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` }, body: JSON.stringify(body) });
      if (!response.ok) { const error = await response.json() as { detail?: unknown };
        throw new Error(`لم تُحفظ المراجعة (${response.status}): ${typeof error.detail === "string" ? error.detail : "راجع المدخلات والصلاحيات"}`); }
      await this.refresh();
    } catch (error) { this.message(String(error)); }
    finally { buttons.forEach(button => button.disabled = false); }
  }
}
