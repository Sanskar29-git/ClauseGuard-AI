
const $=s=>document.querySelector(s);
["A","B"].forEach(k=>$("#file"+k).addEventListener("change",async e=>{
  const f=e.target.files[0];if(!f)return;$("#info"+k).classList.remove("hidden");$("#info"+k).textContent=`✓ ${f.name} · ${(f.size/1024/1024).toFixed(2)} MB`;
  if(/\.(txt|md)$/i.test(f.name))$("#text"+k).value=await f.text();
}));
$("#compareBtn").addEventListener("click",async()=>{
  const a=$("#fileA").files[0],b=$("#fileB").files[0],ta=$("#textA").value.trim(),tb=$("#textB").value.trim();
  if(!a&&!ta)return out("Please provide Contract A.");if(!b&&!tb)return out("Please provide Contract B.");
  const fd=new FormData(); if(a)fd.append("contract_a_file",a);else fd.append("contract_a_text",ta);if(b)fd.append("contract_b_file",b);else fd.append("contract_b_text",tb);
  fd.append("context",$("#compareContext").value);fd.append("priority",$("#priority").value);
  try{const r=await fetch("/api/compare",{method:"POST",body:fd}),x=await r.json();if(!r.ok)throw Error(x.detail||"Comparison failed.");render(x)}catch(e){out(e.message)}
});
function out(m){$("#compareOut").innerHTML=`<div class="panel" style="margin-top:15px;color:#b53e46">${esc(m)}</div>`}
function render(x){
  const diffs=(x.differences||[]).map(d=>`<tr><td><span class="changeTag">${esc(d.type)}</span></td><td>${esc(d.category)}</td><td>${esc(d.a||"Not present")}</td><td>${esc(d.b||"Not present")}</td><td>${esc(d.difference)}</td></tr>`).join("");
  const a=x.a||{},b=x.b||{};
  $("#compareOut").innerHTML=`
  <div class="compareSummary">
    <div class="winner"><small>BETTER MATCH FOR YOU</small><strong>${esc(x.winner||"—")}</strong><p>${esc(x.explanation||"The recommendation is based on the selected priority.")}</p></div>
    <div class="summaryCard"><h3>Contract A Risk Score</h3><p style="font-size:27px;color:#d94e56;font-weight:900">${a.risk??"—"}<small style="font-size:10px;color:#888"> /100</small></p><p>${(a.strengths||[]).slice(0,2).map(esc).join("<br>")}</p></div>
    <div class="summaryCard"><h3>Contract B Risk Score</h3><p style="font-size:27px;color:#3a9d67;font-weight:900">${b.risk??"—"}<small style="font-size:10px;color:#888"> /100</small></p><p>${(b.strengths||[]).slice(0,2).map(esc).join("<br>")}</p></div>
  </div>
  <div class="graphBox" style="margin-top:14px"><h3>Risk Comparison</h3>
    ${riskBar("Financial",a,b,"financial")}${riskBar("Termination",a,b,"termination")}${riskBar("Liability",a,b,"liability")}${riskBar("Privacy",a,b,"privacy")}${riskBar("Renewal",a,b,"renewal")}
  </div>
  <div class="tableWrap"><table class="dataTable"><thead><tr><th>Change</th><th>Category</th><th>Contract A</th><th>Contract B</th><th>Difference</th></tr></thead><tbody>${diffs||"<tr><td colspan='5'>No clause-level differences detected.</td></tr>"}</tbody></table></div>
  <div class="panel" style="margin-top:14px"><h3>Negotiation Suggestions</h3>${(x.negotiation||[]).map(n=>`<div style="font-size:11px;padding:10px 0;border-bottom:1px solid #eee">→ ${esc(n)}</div>`).join("")||"<p style='font-size:11px;color:#777'>No high-priority negotiation point was automatically detected.</p>"}</div>`;
}
function riskBar(label,a,b,key){
  const av=a.categories?.[key]??0,bv=b.categories?.[key]??0,max=Math.max(av,bv,1);
  return `<div class="hbar"><div class="hbarTop"><span>${label}</span><b>A ${av} · B ${bv}</b></div><div class="track"><div class="fill" style="width:${Math.max(av,bv)/max*100}%"></div></div></div>`;
}
