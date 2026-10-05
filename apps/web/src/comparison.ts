type Source = {manuscript_id:string;page_id:string;region_id:string|null};
type Witness = {id:string;label:string;manuscript_id:string|null;kind:string; bibliography:{repository:string|null;shelfmark:string|null;rights:string|null}};
type Variant = {id:string;locus:string;readings:Record<string,string>;note:string|null;sources:Source[]};
type Difference = {operation:string;left:string[];right:string[]};

export class ComparisonPanel {
  private version=0;
  constructor(private root:HTMLElement,private base:()=>string,private openSource:(source:Source)=>Promise<void>) {
    root.innerHTML=`<summary>مقارنة النسخ والتحقيق</summary><p>قارن القراءات المسجلة لنسختين من العمل نفسه. الفروق حرفية؛ لا تعيّن قراءة محققة تلقائيًا ولا تحاذي صفحات غير مرتبطة.</p>
      <form><label>معرّف العمل <input data-work required maxlength="200" /></label><button type="submit">تحميل نسخ العمل</button></form>
      <p data-status role="status"></p><div data-witnesses></div><div data-variants></div>`;
    root.querySelector('form')!.addEventListener('submit',e=>{e.preventDefault();void this.load();});
  }
  private url(work:string,path:string){return `${this.base().replace(/\/$/,'')}/api/v1/scholarship/works/${encodeURIComponent(work)}/${path}`;}
  private async load(){
    const ticket=++this.version,work=this.root.querySelector<HTMLInputElement>('[data-work]')!.value.trim();
    const status=this.root.querySelector<HTMLElement>('[data-status]')!,output=this.root.querySelector<HTMLElement>('[data-variants]')!,witnesses=this.root.querySelector<HTMLElement>('[data-witnesses]')!;
    status.textContent='جارٍ تحميل النسخ والقراءات…';output.replaceChildren();witnesses.replaceChildren();
    try {
      const responses=await Promise.all([fetch(this.url(work,'witnesses')),fetch(this.url(work,'variants'))]);
      if(responses.some(r=>!r.ok))throw new Error('تعذر تحميل النسخ والقراءات.');
      const [items,variants]=await Promise.all(responses.map(r=>r.json())) as [Witness[],Variant[]];
      if(ticket!==this.version)return;
      const labels=new Map(items.map(w=>[w.id,w.label]));
      for(const witness of items){const p=document.createElement('p');p.textContent=`${witness.label} • ${witness.kind} • ${witness.bibliography.repository??'مكان الحفظ غير مسجل'} • ${witness.bibliography.shelfmark??'رقم الحفظ غير مسجل'} • ${witness.bibliography.rights??'الحقوق غير مسجلة'}`;witnesses.append(p);}
      status.textContent=variants.length?'قراءات مسجلة؛ افحص الأصل والدليل قبل الحكم عليها.':'لا توجد قراءات مقارنة مسجلة لهذا العمل.';
      for(const variant of variants){
        const article=document.createElement('article');article.className='region-card';
        const title=document.createElement('h3');title.textContent=variant.locus;article.append(title);
        if(variant.note){const note=document.createElement('p');note.textContent=variant.note;article.append(note);}
        const form=document.createElement('form'),left=document.createElement('select'),right=document.createElement('select');
        const ids=Object.keys(variant.readings).filter(id=>labels.has(id));
        for(const [select,text] of [[left,'النسخة الأولى'],[right,'النسخة الثانية']] as const){
          const label=document.createElement('label');label.textContent=text;
          for(const id of ids){const option=document.createElement('option');option.value=id;option.textContent=labels.get(id)!;select.append(option);}
          label.append(select);form.append(label);
        }
        right.selectedIndex=Math.min(1,ids.length-1);
        const button=document.createElement('button');button.type='submit';button.textContent='قارن القراءتين';button.disabled=ids.length<2;form.append(button);
        const result=document.createElement('div');result.dataset.comparison='';article.append(form,result);
        form.addEventListener('submit',async e=>{
          e.preventDefault();if(left.value===right.value){result.textContent='اختر نسختين مختلفتين.';return;}
          button.disabled=true;result.textContent='جارٍ مقارنة الكلمات…';
          try {
            const response=await fetch(this.url(work,`variants/${encodeURIComponent(variant.id)}/compare?left=${encodeURIComponent(left.value)}&right=${encodeURIComponent(right.value)}`));
            if(!response.ok)throw new Error('تعذرت المقارنة.');
            const data=await response.json() as {method:string;differences:Difference[]};if(ticket!==this.version)return;
            if(data.method!=='literal-word-diff')throw new Error('طريقة مقارنة غير معروفة.');
            result.replaceChildren();
            const columns=document.createElement('div');columns.className='witness-columns';
            for(const id of [left.value,right.value]){const section=document.createElement('section'),heading=document.createElement('h4'),text=document.createElement('p');heading.textContent=labels.get(id)!;text.textContent=variant.readings[id];section.append(heading,text);columns.append(section);}result.append(columns);
            const operations:Record<string,string>={equal:'مطابق',replace:'اختلاف',delete:'في النسخة الأولى فقط',insert:'في النسخة الثانية فقط'};
            for(const diff of data.differences){const p=document.createElement('p');p.textContent=`${operations[diff.operation]??diff.operation}: ${diff.left.join(' ')} ⇄ ${diff.right.join(' ')}`;result.append(p);}
          } catch(error){result.textContent=String(error);}finally{button.disabled=false;}
        });
        const evidence=document.createElement('p');evidence.textContent=variant.sources.length?'مصادر القراءة المسجلة:':'الدليل غير مربوط؛ لا تعرض هذه القراءة كنص موثّق.';article.append(evidence);
        for(const source of variant.sources){const open=document.createElement('button');open.type='button';open.textContent=`افتح الدليل: ${source.manuscript_id} / ${source.page_id}`;open.addEventListener('click',()=>void this.openSource(source));article.append(open);}
        output.append(article);
      }
    }catch(error){if(ticket===this.version)status.textContent=String(error);}
  }
}
