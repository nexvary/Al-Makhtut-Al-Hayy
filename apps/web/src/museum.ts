export class MuseumPanel {
  constructor(private root:HTMLElement, private base:()=>string){
    root.innerHTML=`<summary>المتحف الحي — Living Museum</summary><p>معارض موثقة تربط الرسومات والأدوات بالمصدر. إعادة البناء التفسيرية تظل ظاهرة بهذا الوصف.</p><button type="button">تحميل المعارض</button><div data-exhibitions role="status"></div>`;
    root.querySelector('button')!.addEventListener('click',()=>void this.load());
  }
  private url(path:string){return `${this.base().replace(/\/$/,'')}/api/v1/museum/${path}`;}
  private async load(){
    const output=this.root.querySelector('[data-exhibitions]')!;output.textContent='جارٍ تحميل المعارض…';
    try{
      const response=await fetch(this.url('exhibitions'));if(!response.ok)throw new Error(`تعذر تحميل المعارض (${response.status})`);
      const exhibits=await response.json() as {exhibition_id:string;title:string;description:string;state:string}[];output.replaceChildren();
      if(!exhibits.length)output.textContent='لا توجد معارض موثقة في قاعدة المشروع بعد.';
      for(const exhibit of exhibits){const article=document.createElement('article'), title=document.createElement('h3'),description=document.createElement('p'),button=document.createElement('button'),objects=document.createElement('div');article.className='region-card';
        title.textContent=`${exhibit.title} • ${exhibit.state}`;description.textContent=exhibit.description;button.textContent='ادخل المعرض';
        button.addEventListener('click',async()=>{button.disabled=true;try{
          const response=await fetch(this.url(`exhibitions/${encodeURIComponent(exhibit.exhibition_id)}`));if(!response.ok)throw new Error('تعذر فتح المعرض');
          const result=await response.json() as {objects:{name:string;description:string;evidence_class:string;state:string;interpretation_notes:string|null;
            provenance:{source:{manuscript_id:string;page_id:string;region_id:string}};assets:{kind:string;url:string;evidence_class:string;license:string;attribution:string}[]}[]};objects.replaceChildren();
          for(const object of result.objects){const section=document.createElement('section'), heading=document.createElement('h4'),p=document.createElement('p'),source=document.createElement('small');
            heading.textContent=`${object.name} • ${object.evidence_class==='interpretive_reconstruction'?'إعادة بناء تفسيرية':'دليل موثق'} • ${object.state}`;
            p.textContent=object.description+(object.interpretation_notes?` • الافتراضات: ${object.interpretation_notes}`:'');
            source.textContent=`المصدر: ${object.provenance.source.manuscript_id} / ${object.provenance.source.page_id} / ${object.provenance.source.region_id}`;section.append(heading,p,source);
            for(const asset of object.assets){const line=document.createElement('p'),link=document.createElement('a');link.textContent=`${asset.kind} • ${asset.evidence_class==='interpretive_reconstruction'?'تفسير':'دليل'} • ${asset.license} • ${asset.attribution}`;
              if(/^https?:\/\//.test(asset.url)){link.href=asset.url;link.target='_blank';link.rel='noopener noreferrer';}line.append(link);section.append(line);}
            objects.append(section);
          }
        }catch(error){objects.textContent=String(error);}finally{button.disabled=false;}});article.append(title,description,button,objects);output.append(article);
      }
    }catch(error){output.textContent=String(error);}
  }
}
