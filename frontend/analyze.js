
let latest=null;
const $=s=>document.querySelector(s);

$("#file").addEventListener("change",async e=>{
  const f=e.target.files[0]; if(!f)return;
  $("#fileInfo").classList.remove("hidden");
  $("#fileInfo").textContent=`✓ ${f.name} · ${(f.size/1024/1024).toFixed(2)} MB`;
  if(/\.(txt|md)$/i.test(f.name)) $("#contract").value=await f.text();
});
$("#analyzeBtn").addEventListener("click",async()=>{
  const fd=new FormData(), f=$("#file").files[0], text=$("#contract").value.trim(), context=$("#context").value.trim();
  if(f)fd.append("contract_file",f); else fd.append("contract_text",text);
  fd.append("context",context);
  if(!f&&!text)return showError("Please upload a contract or paste contract text.");
  if(!context)return showError("Please describe your situation so the analysis can be personalized.");
  $("#load").classList.remove("hidden");
  try{
    const r=await fetch("/api/analyze",{method:"POST",body:fd});
    const x=await r.json(); if(!r.ok)throw Error(x.detail||"Analysis failed.");
    latest=x; render(x);
  }catch(e){showError(e.message)}
  finally{$("#load").classList.add("hidden")}
});
function showError(msg){$("#analysis").innerHTML=`<div class="panel" style="margin-top:15px;border-color:#f0c8cb;color:#b53e46">${esc(msg)}</div>`}
function render(x){
  const counts={}; x.clauses.forEach(c=>counts[c.label]=(counts[c.label]||0)+1);
  const max=Math.max(...Object.values(counts),1);
  const bars=Object.entries(counts).map(([k,v])=>`<div class="hbar"><div class="hbarTop"><span>${esc(k)}</span><b>${v}</b></div><div class="track"><div class="fill" style="width:${v/max*100}%"></div></div></div>`).join("");
  const clauses=x.clauses.slice().sort((a,b)=>b.risk-a.risk).slice(0,18).map(c=>`
    <div class="clause ${c.level}">
      <h4>${esc(c.label)} · ${esc(c.title)} <span>${c.risk}/100</span></h4>
      <p>${esc(c.text)}</p>
      <div class="evidence"><b>Evidence:</b> ${esc(c.evidence)}</div>
      <p><b>Context impact:</b> ${esc(c.impact)}</p>
    </div>`).join("");
  const rows=x.clauses.slice().sort((a,b)=>b.risk-a.risk).slice(0,10).map(c=>`<tr><td><strong>${esc(c.title)}</strong></td><td>${esc(c.label)}</td><td>${c.risk}</td><td>${esc(c.level)}</td><td>${c.conflicts?.length?"Yes":"No"}</td></tr>`).join("");
  $("#analysis").innerHTML=`
    <div class="resultHero"><div><h3>Analysis Complete</h3><p>${esc(x.document_name||"Contract")} · ${x.clauses.length} clause segments detected</p></div><div class="resultScore">${x.risk}<small style="font-size:11px;color:#aeb5c8"> / 100</small></div></div>
    <div class="resultsGrid">
      <div class="panel"><div class="panelHead"><div><h3>Priority Findings</h3><small>Ranked by detected exposure</small></div></div>${clauses||"<p>No clauses detected.</p>"}</div>
      <div>
        <div class="graphBox"><h3>Risk by Clause Category</h3>${bars}</div>
        <div class="graphBox" style="margin-top:14px"><h3>Strengths</h3>${(x.strengths||[]).slice(0,5).map(s=>`<div style="font-size:10px;padding:9px 0;border-bottom:1px solid #eee">✓ ${esc(s)}</div>`).join("")||"<div style='font-size:10px;color:#777'>No strong protective signals detected.</div>"}</div>
        <div class="graphBox" style="margin-top:14px"><h3>Top Concerns</h3>${(x.concerns||[]).slice(0,5).map(s=>`<div style="font-size:10px;padding:9px 0;border-bottom:1px solid #eee">⚠ ${esc(s)}</div>`).join("")||"<div style='font-size:10px;color:#777'>No major concerns detected.</div>"}</div>
      </div>
    </div>
    <div class="tableWrap"><table class="dataTable"><thead><tr><th>Clause</th><th>Category</th><th>Risk</th><th>Level</th><th>Context Conflict</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}
