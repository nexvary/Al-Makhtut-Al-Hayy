type Entity = {entity_id:string; name:string; kind:string; state:string; interval:{start_year:number;end_year:number;circa:boolean}|null;
  provenance:{source:{manuscript_id:string;page_id:string}}};
export class HeritagePanel {
  constructor(private root:HTMLElement, private base:()=>string) {
    root.innerHTML=`<summary>المعرفة المترابطة وآلة الزمن</summary>
      <p>اعرض الكيانات والعلاقات المسجلة بمصادرها. البيانات مجهولة التاريخ لا تدخل نتائج الفترة.</p>
      <form data-search><label>اسم أو مصطلح <input data-query maxlength="200" /></label><button type="submit">ابحث في المعرفة</button></form>
      <form data-time><label>من سنة <input data-start type="number" min="-10000" max="3000" value="900" required /></label>
        <label>إلى سنة <input data-end type="number" min="-10000" max="3000" value="1300" required /></label>
        <button type="submit">افتح الفترة</button><button type="button" data-map>أماكن الفترة</button></form>
      <div data-results role="status"></div>`;
    root.querySelector('[data-search]')!.addEventListener('submit',e=>{e.preventDefault();void this.load('entities?q='+encodeURIComponent(this.input('query')));});
    root.querySelector('[data-time]')!.addEventListener('submit',e=>{e.preventDefault();void this.load('time-machine?'+this.years());});
    root.querySelector('[data-map]')!.addEventListener('click',()=>void this.map());
  }
  private input(name:string){return this.root.querySelector<HTMLInputElement>(`[data-${name}]`)!.value;}
  private years(){return `start=${encodeURIComponent(this.input('start'))}&end=${encodeURIComponent(this.input('end'))}`;}
  private url(path:string){return `${this.base().replace(/\/$/,'')}/api/v1/heritage/${path}`;}
  private async load(path:string) {
    const output=this.root.querySelector('[data-results]')!; output.textContent='جارٍ البحث في السجلات…';
    try {
      const response=await fetch(this.url(path)); if(!response.ok)throw new Error(`تعذر البحث (${response.status})`);
      const entities=await response.json() as Entity[]; output.replaceChildren();
      if(!entities.length)output.textContent='لا توجد كيانات موثقة مطابقة في قاعدة المشروع.';
      for(const entity of entities){
        const article=document.createElement('article'), title=document.createElement('h3'), text=document.createElement('p'),button=document.createElement('button'),related=document.createElement('div');
        article.className='region-card';title.textContent=entity.name;
        text.textContent=`${entity.kind} • ${entity.state} • ${entity.interval ? `${entity.interval.start_year}–${entity.interval.end_year}${entity.interval.circa?' (تقريبي)':''}`:'تاريخ غير موثق'} • المصدر: ${entity.provenance.source.manuscript_id} / ${entity.provenance.source.page_id}`;
        button.textContent='اعرض العلاقات الموثقة';button.addEventListener('click',async()=>{
          button.disabled=true;
          try {const response=await fetch(this.url(`entities/${encodeURIComponent(entity.entity_id)}`));if(!response.ok)throw new Error('تعذر تحميل العلاقات');
            const graph=await response.json() as {entities:Entity[];relations:{subject:string;predicate:string;object:string;state:string}[]};related.replaceChildren();
            const names=new Map(graph.entities.map(e=>[e.entity_id,e.name]));
            if(!graph.relations.length)related.textContent='لا توجد علاقات موثقة لهذا الكيان بعد.';
            for(const edge of graph.relations){const p=document.createElement('p');p.textContent=`${names.get(edge.subject)??edge.subject} → ${edge.predicate} → ${names.get(edge.object)??edge.object} • ${edge.state}`;related.append(p);}
          }catch(error){related.textContent=String(error);}finally{button.disabled=false;}
        });article.append(title,text,button,related);output.append(article);
      }
    }catch(error){output.textContent=String(error);}
  }
  private async map(){
    const output=this.root.querySelector('[data-results]')!;
    try{
      const response=await fetch(this.url('map?'+this.years()));if(!response.ok)throw new Error(`تعذر تحميل الأماكن (${response.status})`);
      const data=await response.json() as {features:{geometry:{coordinates:[number,number]};properties:{name:string;approximate:boolean;state:string}}[]};
      output.replaceChildren();if(!data.features.length)output.textContent='لا توجد إحداثيات موثقة في هذه الفترة.';
      for(const feature of data.features){const p=document.createElement('p'),link=document.createElement('a');
        const [lon,lat]=feature.geometry.coordinates;link.textContent=`${feature.properties.name} • ${lat}, ${lon}${feature.properties.approximate?' (موقع تقريبي)':''} • ${feature.properties.state}`;
        link.href=`https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=8/${lat}/${lon}`;link.target='_blank';link.rel='noopener noreferrer';p.append(link);output.append(p);}
    }catch(error){output.textContent=String(error);}
  }
}
