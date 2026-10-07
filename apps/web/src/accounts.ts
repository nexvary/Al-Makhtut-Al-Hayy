type Account={id:string;username:string;role:string;active:number;version:number};
export class AccountsPanel {
  private token='';
  private sessionBase='';
  private loggingIn=false;
  constructor(private root:HTMLElement,private base:()=>string) {
    root.innerHTML=`<summary>حساب المستخدم والصلاحيات</summary>
      <p>جلسة مؤقتة؛ لا تحفظ كلمة المرور أو الرمز في المتصفح. ينشئ المسؤول الحساب الأول على الخادم.</p>
      <form data-login><label>اسم المستخدم <input data-username autocomplete="username" required minlength="3" maxlength="100" /></label>
      <label>كلمة المرور <input data-password type="password" autocomplete="current-password" required maxlength="1024" /></label>
      <button type="submit">تسجيل الدخول</button><button type="button" data-logout disabled>تسجيل الخروج</button></form>
      <p data-status role="status"></p>
      <details data-admin hidden><summary>إدارة المستخدمين</summary>
      <form data-create><label>اسم المستخدم الجديد <input data-new-name required minlength="3" maxlength="100" /></label>
      <label>كلمة المرور الجديدة <input data-new-password type="password" required minlength="12" maxlength="1024" autocomplete="new-password" /></label>
      <label>الدور <select data-new-role><option value="reader">قارئ</option><option value="student">طالب</option><option value="researcher">باحث</option><option value="reviewer">مراجع</option><option value="editor">محرر</option><option value="admin">مسؤول</option></select></label>
      <button type="submit">إنشاء المستخدم</button></form><button data-refresh type="button">تحميل المستخدمين</button>
      <div data-users></div></details>`;
    document.querySelector('#apiBase')!.addEventListener('input',()=>{if(this.token && this.base().trim().replace(/\/$/,'')!==this.sessionBase){this.session('');this.root.querySelector<HTMLElement>('[data-admin]')!.hidden=true;}});
    root.querySelector('[data-login]')!.addEventListener('submit',e=>{e.preventDefault();void this.login();});
    root.querySelector('[data-logout]')!.addEventListener('click',()=>void this.logout());
    root.querySelector('[data-create]')!.addEventListener('submit',e=>{e.preventDefault();void this.create();});
    root.querySelector('[data-refresh]')!.addEventListener('click',()=>void this.users());
  }
  private input(name:string){return this.root.querySelector<HTMLInputElement>(`[data-${name}]`)!;}
  private status(text:string){this.root.querySelector('[data-status]')!.textContent=text;}
  private async request(path:string,body?:unknown,method='POST'){
    const endpoint=new URL(this.base());
    if(endpoint.protocol!=='https:' && !(endpoint.protocol==='http:' && ['localhost','127.0.0.1','[::1]'].includes(endpoint.hostname)))throw new Error('يتطلب تسجيل الدخول HTTPS، باستثناء الخادم المحلي للتطوير.');
    if(this.token && this.base().trim().replace(/\/$/,'')!==this.sessionBase){this.session('');throw new Error('تغير الخادم؛ سجّل الدخول من جديد.');}
    const response=await fetch(`${this.base().replace(/\/$/,'')}/api/v1/accounts${path}`,{method,headers:{'Content-Type':'application/json',...(this.token?{Authorization:`Bearer ${this.token}`}:{})},...(body!==undefined?{body:JSON.stringify(body)}:{})});
    if(!response.ok)throw new Error(`تعذرت العملية (${response.status}). تحقق من البيانات أو الصلاحية.`);
    return response.json();
  }
  private session(token:string){
    this.token=token;this.sessionBase=token?this.base().trim().replace(/\/$/,''):'';document.querySelectorAll<HTMLInputElement>('[data-token]').forEach(input=>input.value=token);
    this.root.querySelector<HTMLButtonElement>('[data-logout]')!.disabled=!token;
  }
  private async login(){
    if(this.loggingIn)return;this.loggingIn=true;const originalBase=this.base();this.session('');this.root.querySelector<HTMLElement>('[data-admin]')!.hidden=true;
    try{const result=await this.request('/login',{username:this.input('username').value,password:this.input('password').value});
      if(originalBase!==this.base())throw new Error('تغير الخادم أثناء الدخول.');
      this.session(result.access_token);this.input('password').value='';
      this.root.querySelector<HTMLElement>('[data-admin]')!.hidden=result.account.role!=='admin';
      this.status(`تم الدخول: ${result.account.username}`);
    }catch(error){this.status(String(error));}
    finally{this.loggingIn=false;}
  }
  private async logout(){
    try{await this.request('/logout');this.status('تم الخروج وإبطال الجلسات.');}
    catch{this.status('تم مسح الجلسة محليًا؛ تعذر تأكيد إبطالها على الخادم.');}
    finally{this.session('');this.root.querySelector<HTMLElement>('[data-admin]')!.hidden=true;this.root.querySelector('[data-users]')!.replaceChildren();}
  }
  private async create(){
    try{await this.request('',{username:this.input('new-name').value,password:this.input('new-password').value,role:this.root.querySelector<HTMLSelectElement>('[data-new-role]')!.value});
      this.input('new-password').value='';this.status('تم إنشاء المستخدم.');await this.users();
    }catch(error){this.status(String(error));}
  }
  private async users(){
    try{
      const accounts=await this.request('',undefined,'GET') as Account[],list=this.root.querySelector('[data-users]')!;list.replaceChildren();
      for(const account of accounts){
        const article=document.createElement('details'),title=document.createElement('summary');title.textContent=`${account.username} • ${account.role} • ${account.active?'نشط':'معطل'}`;article.append(title);
        const select=document.createElement('select');select.setAttribute('aria-label',`دور ${account.username}`);
        for(const [role,label] of [['reader','قارئ'],['student','طالب'],['researcher','باحث'],['reviewer','مراجع'],['editor','محرر'],['admin','مسؤول'],['viewer','مشاهد'],['transcriber','ناسخ']]){
          const option=document.createElement('option');option.value=role;option.textContent=label;select.append(option);
        }select.value=account.role;
        const save=document.createElement('button');save.type='button';save.textContent='حفظ الدور';
        const toggle=document.createElement('button');toggle.type='button';toggle.textContent=account.active?'تعطيل الحساب':'تفعيل الحساب';
        const reset=document.createElement('input');reset.type='password';reset.minLength=12;reset.maxLength=1024;reset.autocomplete='new-password';reset.placeholder='كلمة مرور بديلة';reset.setAttribute('aria-label',`كلمة مرور ${account.username}`);
        const resetButton=document.createElement('button');resetButton.type='button';resetButton.textContent='تغيير كلمة المرور';
        const update=async(body:unknown)=>{
          save.disabled=toggle.disabled=resetButton.disabled=true;
          try{await this.request(`/${encodeURIComponent(account.id)}`,body,'PATCH');reset.value='';this.status('تم التحديث وإبطال الجلسات السابقة.');await this.users();}
          catch(error){this.status(String(error));save.disabled=toggle.disabled=resetButton.disabled=false;}
        };
        save.addEventListener('click',()=>void update({role:select.value}));toggle.addEventListener('click',()=>void update({active:!account.active}));
        resetButton.addEventListener('click',()=>{if(reset.value.length<12){this.status('كلمة المرور تحتاج 12 حرفًا على الأقل.');return;}void update({password:reset.value});});
        article.append(select,save,toggle,reset,resetButton);list.append(article);
      }
    }catch(error){this.status(String(error));}
  }
}
