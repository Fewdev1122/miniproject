class Register {
  constructor(formId) {
    this.form = document.getElementById(formId)
    this.init();
  }

  init()  {
    if(this.form){
      this.form.addEventListener("submit", (e) => this.handleSummit(e));
    }
  }
  handleSummit(e){
    const email = this.form.email.value.trim();
    const password = this.form.password.value.trim();
    const code = this.form.code.value.trim();
    const confirm = this.form.confirm.value.trim();

    if(!this.checkemail(email)){
      e.preventDefault();
      alert("อีเมลไม่ถูกต้อง")
      return;
    }
    if(password.length < 4){
      e.preventDefault();
      alert("รหัสผ่านอย่างน้อย 4 ตัว")
    }
    if(code !== "1234"){
      e.preventDefault();
      alert("รหัสร้านไม่ถูกต้อง")
    }
    if(password !== confirm){
      e.preventDefault();
      alert("รหัสผ่านไม่ตรงกัน")
    }
  }
  checkemail(email){
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email); 
  }
}
document.addEventListener('DOMContentLoaded',() => {
  const register = new Register('form-register');
});