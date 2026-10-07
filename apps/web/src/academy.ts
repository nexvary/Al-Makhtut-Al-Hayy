import type { Manuscript, ManuscriptPage } from './types';
type Context = { base: string; manuscript: Manuscript | null; page: ManuscriptPage | null };
export class AcademyPanel {
  private version = 0;
  constructor(private root: HTMLElement, private context: () => Context) {
    root.innerHTML = `<summary>أكاديمية العثمانية والقاموس</summary>
      <p>تعلّم من المصدر: حاول القراءة، ثم اكشف المراحل المراجعة تدريجيًا. المواد التعليمية تحتاج مصدرًا وحقوق استخدام مسجلة.</p>
      <form data-dictionary><label>ابحث في القاموس الموثق <input data-query required maxlength="200" /></label><button type="submit">بحث</button></form>
      <div data-definitions role="status"></div>
      <button type="button" data-refresh>تحميل تمارين الصفحة</button>
      <p data-status role="status"></p><div data-exercises></div>`;
    root.querySelector('[data-refresh]')!.addEventListener('click', () => void this.refresh());
    root.querySelector('form')!.addEventListener('submit', event => { event.preventDefault(); void this.search(); });
  }
  private async search() {
    const container = this.root.querySelector('[data-definitions]')!; container.replaceChildren();
    const query = this.root.querySelector<HTMLInputElement>('[data-query]')!.value;
    try {
      const response = await fetch(`${this.context().base.replace(/\/$/,'')}/api/v1/ottoman/dictionary?q=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error(`تعذر البحث (${response.status})`);
      const entries = await response.json() as { spelling: string; transliteration: string | null; modern_turkish: string | null; arabic: string | null; english: string | null;
        state: string; linguistic_origin: string | null; provenance: { source: { manuscript_id: string; page_id: string }; confidence: number | null } }[];
      if (!entries.length) container.textContent = 'لا توجد مادة موثقة مطابقة. لا تُختلق معاني أو أصول لغوية.';
      for (const entry of entries) {
        const article = document.createElement('article'); article.className = 'region-card';
        const lines = [entry.spelling, entry.transliteration, entry.modern_turkish, entry.arabic, entry.english,
          `الحالة: ${entry.state} • الثقة: ${entry.provenance.confidence ?? 'غير معروفة'}`,
          `المصدر: ${entry.provenance.source.manuscript_id} / ${entry.provenance.source.page_id}`,
          entry.linguistic_origin ? `الأصل اللغوي الموثق: ${entry.linguistic_origin}` : 'الأصل اللغوي: غير موثق'];
        for (const line of lines.filter(Boolean)) { const p = document.createElement('p'); p.textContent = line; p.dir = 'auto'; article.append(p); }
        container.append(article);
      }
    } catch (error) { container.textContent = String(error); }
  }
  async refresh() {
    const ticket = ++this.version, context = this.context();
    const status = this.root.querySelector('[data-status]')!, list = this.root.querySelector('[data-exercises]')!;
    list.replaceChildren();
    if (!context.manuscript || !context.page) { status.textContent = 'اربط صفحة من الخادم لعرض تمارينها.'; return; }
    const url = `${context.base.replace(/\/$/,'')}/api/v1/ottoman/manuscripts/${encodeURIComponent(context.manuscript.id)}/pages/${encodeURIComponent(context.page.id)}/exercises`;
    try {
      const response = await fetch(url); if (!response.ok) throw new Error(`تعذر تحميل التمارين (${response.status})`);
      const exercises = await response.json() as {id:string; title:string; rights_note:string}[];
      if (ticket !== this.version) return;
      status.textContent = exercises.length ? 'انظر إلى الأصل ثم جرّب القراءة.' : 'لا توجد تمارين مراجعة لهذه الصفحة بعد.';
      for (const exercise of exercises) {
        const form = document.createElement('form'), heading = document.createElement('h3'), input = document.createElement('textarea');
        const submit = document.createElement('button'), reveal = document.createElement('button'), output = document.createElement('div'), note = document.createElement('small');
        heading.textContent = exercise.title; input.setAttribute('aria-label','محاولة قراءة النص العثماني'); input.maxLength = 100000;
        submit.textContent = 'تحقق من المحاولة'; reveal.textContent = 'اكشف المرحلة التالية'; reveal.type = 'button'; note.textContent = exercise.rights_note;
        let step = 0;
        const attempt = async () => {
          submit.disabled = reveal.disabled = true;
          try {
            const response = await fetch(`${url}/${encodeURIComponent(exercise.id)}/attempt`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text:input.value,reveal_step:step})});
            if (!response.ok) throw new Error(`تعذر فحص المحاولة (${response.status})`);
            const result = await response.json() as { exact_match:boolean; available_steps:number; revealed:{stage:string;text:string}[] };
            output.replaceChildren(); const feedback = document.createElement('p');
            feedback.textContent = result.exact_match ? 'مطابقة للنص المراجع. هذا تدريب، وليس اعتمادًا علميًا.' : 'ليست مطابقة حرفية. قارن بالمراحل المراجعة؛ قد تحتاج قراءتك إلى مناقشة بشرية.';
            output.append(feedback);
            for (const item of result.revealed) {const p=document.createElement('p'); p.textContent=`${item.stage}: ${item.text}`;p.dir='auto';output.append(p);}
            reveal.hidden = step >= result.available_steps;
          } catch (error) { output.textContent = String(error); }
          finally { submit.disabled = reveal.disabled = false; }
        };
        form.addEventListener('submit',event=>{event.preventDefault();void attempt();});
        reveal.addEventListener('click',()=>{step=Math.min(4,step+1);void attempt();});
        form.append(heading,input,submit,reveal,note,output);list.append(form);
      }
    } catch(error) { if(ticket===this.version)status.textContent=String(error); }
  }
}
