import type { Manuscript, ManuscriptPage, Region } from "./types";
type Context = { base: string; manuscript: Manuscript | null; page: ManuscriptPage | null; region: Region | null };
type Record = { id: string; stage: string; state: string; text: string | null; input_revision_id: string | null;
  provenance: { source: { region_id: string | null; witness_id: string | null }; confidence: number | null; reviewer: string | null } };
const labels: { [key: string]: string } = { layout: "تحليل التخطيط", htr: "قراءة آلية HTR/OCR", transcription: "النص العثماني",
  transliteration: "النقل بالحروف اللاتينية", modernization: "التركية الحديثة", translation_ar: "ترجمة عربية", translation_en: "ترجمة إنجليزية" };
const predecessor: { [key: string]: string } = { htr: "layout", transcription: "htr", transliteration: "transcription",
  modernization: "transliteration", translation_ar: "modernization", translation_en: "modernization" };
export class OttomanPanel {
  private records: Record[] = [];
  private version = 0;
  constructor(private root: HTMLElement, private context: () => Context) {
    root.innerHTML = `<summary>المختبر العثماني — Ottoman Lab</summary>
      <p>الأصل العثماني والنقل اللاتيني والتحديث والترجمة مراحل منفصلة. لا توجد خدمة ترجمة آلية متصلة حاليًا.</p>
      <button type="button" data-refresh>تحميل مسار الصفحة</button><p data-message role="status"></p><div data-history></div>
      <form><label>رمز دخول المحرر <input type="password" data-token autocomplete="off" /></label>
        <label>المرحلة <select data-stage>${Object.entries(labels).filter(([k]) => k !== "layout").map(([k,v]) => `<option value="${k}" ${k === "transcription" ? "selected" : ""}>${v}</option>`).join("")}</select></label>
        <label>المراجعة المصدرية <select data-input><option value="">قراءة بشرية مباشرة من الأصل</option></select></label>
        <label>النص <textarea data-text required rows="4" maxlength="100000"></textarea></label>
        <label>حالة المراجعة <select data-state><option value="draft">مسودة</option><option value="machine">آلي</option><option value="verified">محقق بشريًا</option></select></label>
        <label>النموذج للنتيجة الآلية <input data-model maxlength="200" /></label>
        <label>هوية المراجع للاعتماد <input data-reviewer maxlength="200" /></label>
        <button type="submit">حفظ مرحلة مستقلة</button></form>`;
    root.querySelector('[data-refresh]')!.addEventListener('click', () => void this.refresh());
    this.input('stage').addEventListener('change', () => this.updateInputs());
    root.querySelector('form')!.addEventListener('submit', event => { event.preventDefault(); void this.save(); });
  }
  private input(name: string) { return this.root.querySelector<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>(`[data-${name}]`)!; }
  private message(text: string) { this.root.querySelector('[data-message]')!.textContent = text; }
  private scoped() { const region = this.context().region?.id ?? null; return this.records.filter(r => r.provenance.source.region_id === region && !r.provenance.source.witness_id); }
  private updateInputs() {
    const select = this.input('input') as HTMLSelectElement, stage = this.input('stage').value;
    select.replaceChildren();
    if (stage === 'transcription') select.add(new Option('قراءة بشرية مباشرة من الأصل', ''));
    for (const r of this.scoped().filter(r => r.stage === predecessor[stage])) select.add(new Option(`${labels[r.stage]} • ${r.state} • ${r.id.slice(0,8)}`, r.id));
    this.input('state').value = stage === 'htr' ? 'machine' : 'draft';
  }
  async refresh() {
    const ticket = ++this.version, context = this.context(); this.records = [];
    const list = this.root.querySelector('[data-history]')!; list.replaceChildren();
    this.root.querySelector('form')!.hidden = !context.page;
    if (!context.manuscript || !context.page) { this.message('اربط صفحة من الخادم لبدء مسار عثماني موثق.'); this.updateInputs(); return; }
    try {
      const response = await fetch(`${context.base.replace(/\/$/, '')}/api/v1/ottoman/manuscripts/${encodeURIComponent(context.manuscript.id)}/pages/${encodeURIComponent(context.page.id)}`);
      if (!response.ok) throw new Error(`تعذر تحميل المسار (${response.status})`);
      const result = await response.json() as { revisions: Record[] };
      if (ticket !== this.version) return;
      this.records = result.revisions; this.updateInputs();
      this.message(this.scoped().length ? 'المراحل المحفوظة للمنطقة المحددة، مع بقاء الأصل متاحًا.' : 'لا توجد مراحل محفوظة لهذه المنطقة.');
      for (const r of this.scoped()) {
        const article = document.createElement('article'); article.className = 'region-card';
        const title = document.createElement('h3'), text = document.createElement('p'), meta = document.createElement('small');
        title.textContent = `${labels[r.stage]} • ${r.state}`; text.textContent = r.text ?? 'تخطيط الصفحة';
        text.dir = ['transliteration','modernization','translation_en'].includes(r.stage) ? 'ltr' : 'rtl';
        meta.textContent = `الثقة: ${r.provenance.confidence ?? 'غير معروفة'} • المراجع: ${r.provenance.reviewer ?? 'لم يُراجع'} • المصدر: ${r.input_revision_id ?? 'الصورة الأصلية'}`;
        article.append(title,text,meta); list.append(article);
      }
    } catch (error) { if (ticket === this.version) this.message(String(error)); }
  }
  private async save() {
    const context = this.context(), stage = this.input('stage').value, state = this.input('state').value;
    if (!context.manuscript || !context.page || !this.input('token').value.trim()) { this.message('اختر صفحة وأدخل رمز دخول صالحًا.'); return; }
    const prior = this.scoped().filter(r => r.stage === stage).at(-1);
    const button = this.root.querySelector<HTMLButtonElement>('form button')!; button.disabled = true;
    try {
      const response = await fetch(`${context.base.replace(/\/$/, '')}/api/v1/ottoman/revisions`, { method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${this.input('token').value.trim()}` },
        body: JSON.stringify({ stage, state, text: this.input('text').value, parent_revision_id: prior?.id ?? null,
          input_revision_id: this.input('input').value || null,
          provenance: { source: { manuscript_id: context.manuscript.id, page_id: context.page.id,
            region_id: context.region?.id ?? null, coordinates: context.region?.polygon ?? [], source_uri: context.page.canvas_uri ?? context.page.image },
            extraction_method: state === 'machine' ? 'imported-model-output' : 'manual', model: this.input('model').value.trim() || null,
            reviewer: state === 'verified' ? this.input('reviewer').value.trim() : null,
            evidence: [{ manuscript_id: context.manuscript.id, page_id: context.page.id, region_id: context.region?.id ?? null }] } }) });
      if (!response.ok) { const error = await response.json(); throw new Error(`لم تُحفظ المرحلة (${response.status}): ${typeof error.detail === 'string' ? error.detail : 'راجع النص والمصدر وحالة المراجعة'}`); }
      await this.refresh();
    } catch (error) { this.message(String(error)); }
    finally { button.disabled = false; }
  }
}
