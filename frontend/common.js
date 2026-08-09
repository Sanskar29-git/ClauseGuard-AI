
function go(url){ window.location.href=url; }

document.addEventListener("DOMContentLoaded",()=>{
  document.querySelectorAll("[data-faq]").forEach(btn=>{
    btn.addEventListener("click",()=>btn.parentElement.classList.toggle("open"));
  });
  document.querySelectorAll(".priority").forEach(btn=>{
    btn.addEventListener("click",()=>btn.classList.toggle("active"));
  });
});
function esc(s){
  return String(s ?? "").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
}
