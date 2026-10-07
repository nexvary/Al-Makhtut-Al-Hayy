import type { Manuscript, ManuscriptPage, Region } from './types';
type Context = {base:string; manuscript:Manuscript|null; page:ManuscriptPage|null; region:Region|null};
type Match = {index_id:string; similarity:number; source_license:string; provenance:{source:{manuscript_id:string;page_id:string;region_id:string|null}}};

export class VisualSearchPanel {
  private version=0;
  constructor(private root:HTMLElement,private context:()=>Context, private openSource:(source:Match["provenance"]["source"])=>Promise<void>) {
    root.innerHTML=`<summary>اكتشاف التشابه البصري</summary>
      <p>قارن صورة أو رسمًا بصور صغيرة مفهرسة. التشابه ليس إثباتًا لهوية المخطوط أو ناسخه، ولا يحلل الخط أو معنى الصورة.</p>
      <form><label>صورة PNG أو JPEG، حتى 1 ميجابايت و1 ميجابكسل <input data-image type="file" accept="image/png,image/jpeg" required /></label>
      <label>نوع المقارنة <select data-kind><option value="fragment">جزء من الصفحة</option><option value="illustration">رسم</option></select></label>
      <button type="submit">ابحث بالصورة</button></form>
      <details><summary>فهرسة صورة المصدر للمراجعين</summary>
      <p>أقرّ بأن الصورة المختارة مقتطف من الأصل المعروض وأن حقوق المصدر تسمح بالفهرسة. لا يتم تنزيل الأصل الخارجي أو الاحتفاظ بالصورة المرفوعة.</p>
      <label>رمز المراجع <input data-token type="password" autocomplete="off" /></label>
      <label>بيان حقوق الاستخدام <input data-rights maxlength="2000" /></label>
      <button type="button" data-publish>فهرسة المقتطف من المصدر</button></details>
      <p data-status role="status"></p><div data-matches></div>`;
    root.querySelector('form')!.addEventListener('submit',e=>{e.preventDefault();void this.perform(false);});
    root.querySelector('[data-publish]')!.addEventListener('click',()=>void this.perform(true));
  }
  private async image() {
    const file=this.root.querySelector<HTMLInputElement>('[data-image]')!.files?.[0];
    if(!file || !['image/png','image/jpeg'].includes(file.type) || file.size>1048576)throw new Error('اختر PNG أو JPEG لا يتجاوز 1 ميجابايت.');
    const bitmap=await createImageBitmap(file);
    try {if(bitmap.width*bitmap.height>1048576 || bitmap.width>4096 || bitmap.height>4096)throw new Error('صغّر المقتطف إلى مليون بكسل أو أقل.');}
    finally {bitmap.close();}
    const data=new Uint8Array(await file.arrayBuffer());
    let binary='';for(let i=0;i<data.length;i+=8192)binary+=String.fromCharCode(...data.subarray(i,i+8192));
    return btoa(binary);
  }
  private async perform(publish:boolean) {
    const ticket=++this.version, context=this.context();
    const status=this.root.querySelector<HTMLElement>('[data-status]')!, results=this.root.querySelector<HTMLElement>('[data-matches]')!;
    const buttons=this.root.querySelectorAll<HTMLButtonElement>('button');buttons.forEach(b=>b.disabled=true);
    results.replaceChildren();status.textContent='جاري المقارنة…';
    try {
      const image_base64=await this.image(),kind=this.root.querySelector<HTMLSelectElement>('[data-kind]')!.value;
      const body:Record<string,unknown>={image_base64,kind};
      const headers:Record<string,string>={'Content-Type':'application/json'};
      if(publish) {
        if(!context.manuscript || !context.page || !context.manuscript.license)throw new Error('اربط صفحة ذات حقوق مسجلة أولًا.');
        const token=this.root.querySelector<HTMLInputElement>('[data-token]')!.value.trim(), rights=this.root.querySelector<HTMLInputElement>('[data-rights]')!.value.trim();
        if(!token || !rights)throw new Error('يلزم رمز المراجع وبيان الحقوق.');
        headers.Authorization=`Bearer ${token}`;
        body.source_license=context.manuscript.license;body.rights_note=rights;
        body.provenance={source:{manuscript_id:context.manuscript.id,page_id:context.page.id,region_id:context.region?.id??null,source_uri:context.page.image},extraction_method:'curated-thumbnail'};
      }
      const response=await fetch(`${context.base.replace(/\/$/,'')}/api/v1/visual-search/${publish?'index':'query'}`,{method:'POST',headers,body:JSON.stringify(body)});
      if(!response.ok)throw new Error(`تعذرت العملية (${response.status}). تحقق من الصورة والحقوق والصلاحية.`);
      const result=await response.json();if(ticket!==this.version)return;
      if(publish){status.textContent='تمت فهرسة البصمة مع مصدرها وحقوقها.';return;}
      const matches=result.matches as Match[];
      status.textContent=matches.length?'نتائج مرشحة؛ يلزم فحص الأصل بشريًا.':'لا يوجد تشابه ضمن الصور المفهرسة. لا يعني ذلك عدم وجود نظير في العالم.';
      for(const match of matches){
        const article=document.createElement('article');article.className='region-card';
        const anchor=match.provenance.source;
        for(const text of [`المصدر: ${anchor.manuscript_id} / ${anchor.page_id} / ${anchor.region_id??'الصفحة كاملة'}`,`درجة التشابه البصري: ${match.similarity.toFixed(3)}؛ ليست ثقة علمية`,`الحقوق: ${match.source_license}`]){
          const p=document.createElement('p');p.textContent=text;article.append(p);
        }
        const open=document.createElement('button');open.type='button';open.textContent='افتح المخطوط الأصلي';
        open.addEventListener('click',()=>{
          void this.openSource(anchor);
        });article.append(open);results.append(article);
      }
    } catch(error){if(ticket===this.version)status.textContent=String(error);}
    finally{if(ticket===this.version)buttons.forEach(b=>b.disabled=false);}
  }
}
