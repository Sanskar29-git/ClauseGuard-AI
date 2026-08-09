from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import re
from .config import FRONTEND,MAX_FILE_SIZE
from .parser import extract,clean
from .engine import analyze,compare

app=FastAPI(title="ClauseGuard AI",version="2.0")
app.mount("/static",StaticFiles(directory=FRONTEND),name="static")

def get_content(file:Optional[UploadFile],text:Optional[str]):
    if file:
        data=file.file.read()
        if len(data)>MAX_FILE_SIZE: raise HTTPException(413,"File exceeds 20 MB.")
        try: return clean(extract(data,file.filename or "contract.pdf")),file.filename or "Uploaded contract"
        except ValueError as e: raise HTTPException(400,str(e))
    if text and text.strip(): return clean(text),"Pasted contract"
    raise HTTPException(400,"Provide a file or contract text.")

@app.get("/")
def home():
    return FileResponse(FRONTEND / "index.html")

@app.get("/analyze.html")
def analyze_page():
    return FileResponse(FRONTEND / "analyze.html")

@app.get("/compare.html")
def compare_page():
    return FileResponse(FRONTEND / "compare.html")

@app.get("/faq.html")
def faq_page():
    return FileResponse(FRONTEND / "faq.html")

@app.get("/api/health")
def health(): return {"status":"ok"}

@app.post("/api/analyze")
async def api_analyze(contract_file:Optional[UploadFile]=File(None),contract_text:Optional[str]=Form(None),context:str=Form("")):
    text,name=get_content(contract_file,contract_text)
    r=analyze(text,context); r["document_name"]=name
    return r

@app.post("/api/compare")
async def api_compare(contract_a_file:Optional[UploadFile]=File(None),contract_a_text:Optional[str]=Form(None),contract_b_file:Optional[UploadFile]=File(None),contract_b_text:Optional[str]=Form(None),context:str=Form(""),priority:str=Form("balanced")):
    a,an=get_content(contract_a_file,contract_a_text); b,bn=get_content(contract_b_file,contract_b_text)
    r=compare(a,b,context,priority);r["name_a"]=an;r["name_b"]=bn;return r

@app.post("/api/ask")
async def ask(question:str=Form(...),analysis_json:str=Form(...)):
    import json
    try: data=json.loads(analysis_json)
    except: raise HTTPException(400,"Invalid analysis.")
    q=question.lower(); cs=data.get("clauses",[])
    if re.search(r"money|cost|pay|financial",q): selected=[c for c in cs if c["category"]=="financial"]
    elif re.search(r"leave|cancel|terminate|exit|early",q): selected=[c for c in cs if c["category"]=="termination"]
    elif "renew" in q: selected=[c for c in cs if c["category"]=="renewal"]
    elif re.search(r"positive|good|strength",q): selected=[c for c in cs if c["positive"]]
    else: selected=sorted(cs,key=lambda c:c["risk"],reverse=True)[:3]
    selected=selected or sorted(cs,key=lambda c:c["risk"],reverse=True)[:3]
    return {"answer":" ".join(f"{c['title']}: {c['impact']} Evidence: {c['evidence']}" for c in selected[:4]),"evidence":[c["evidence"] for c in selected[:4]]}
