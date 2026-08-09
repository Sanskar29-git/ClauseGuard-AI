import re
from typing import List, Dict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .config import PRIORITIES

CATS={
"financial":[r"\brent\b",r"\bpayment\b",r"\bfee\b",r"\bprice\b",r"\bcost\b",r"\bdeposit\b",r"\bpenalt",r"\binterest\b",r"\brefund\b",r"\bcommission\b",r"\bexpense\b",r"\bincrease\b",r"\bescalat",r"\bamount\b"],
"termination":[r"\bterminat",r"\bcancel",r"\bearly termination\b",r"\bnotice\b",r"\bwithdraw\b",r"\bexit\b"],
"renewal":[r"\brenew",r"\bextension\b",r"\bextend\b",r"\bauto.?renew",r"\bautomatically renew"],
"liability":[r"\bliabil",r"\bindemn",r"\bdamage",r"\bloss\b",r"\bclaim\b",r"\bhold harmless\b",r"\blimit.*liabil"],
"obligations":[r"\bshall\b",r"\bmust\b",r"\brequired\b",r"\bresponsible\b",r"\bobligation\b",r"\bduty\b"],
"restrictions":[r"\bprohibit",r"\brestrict",r"\bnot permitted\b",r"\bmay not\b",r"\bwithout prior written consent\b",r"\bexclusive\b"],
"privacy":[r"\bpersonal data\b",r"\bpersonal information\b",r"\bprivacy\b",r"\bdata processing\b",r"\bdata protection\b",r"\bshare.*third party"],
"ip":[r"\bintellectual property\b",r"\bcopyright\b",r"\btrademark\b",r"\bpatent\b",r"\bwork product\b",r"\bownership\b"],
"disputes":[r"\barbitration\b",r"\bjurisdiction\b",r"\bgoverning law\b",r"\bdispute\b",r"\bmediation\b"],
}

LABELS={"financial":"Financial","termination":"Termination","renewal":"Renewal","liability":"Liability","obligations":"Obligations","restrictions":"Restrictions","privacy":"Privacy","ip":"Intellectual property","disputes":"Disputes","general":"General"}

def split_clauses(text:str)->List[str]:
    text=re.sub(r"[ \t]+"," ",text)
    parts=re.split(r"(?=(?:^|\n)\s*(?:\d+[\.\)]|[A-Z][\.\)]|ARTICLE\s+\w+|SECTION\s+\w+)\s+)",text,flags=re.I)
    parts=[re.sub(r"\s+"," ",p).strip(" -") for p in parts if len(p.strip())>=30]
    if len(parts)<2:
        parts=re.split(r"(?<=[.!?])\s+(?=[A-Z])",text)
        parts=[p.strip() for p in parts if len(p.strip())>=30]
    return parts[:300]

def category(t):
    low=t.lower()
    scores={k:sum(bool(re.search(p,low,re.I)) for p in ps) for k,ps in CATS.items()}
    return max(scores,key=scores.get) if scores and max(scores.values()) else "general"

def features(t):
    low=t.lower()
    nums=[]
    for m in re.findall(r"(?:₹|rs\.?|inr|\$|€|£)\s?[\d,]+(?:\.\d+)?",t,re.I):
        try: nums.append(float(re.sub(r"[^\d.]","",m)))
        except: pass
    pct=[float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*%",t)]
    days=[int(x) for x in re.findall(r"(\d+)\s*(?:day|days)",t,re.I)]
    months=[int(x) for x in re.findall(r"(\d+)\s*(?:month|months)",t,re.I)]
    return {
        "money":max(nums,default=0),"pct":max(pct,default=0),"days":max(days,default=0),
        "months":max(months,default=0),"unilateral":int(bool(re.search(r"sole discretion|may .* without|unilater",low))),
        "auto":int(bool(re.search(r"auto.?renew|automatically renew",low))),
        "negative":len(re.findall(r"penalt|forfeit|indemn|liabil|prohibit|late fee|waive|sole discretion",low)),
        "protective":len(re.findall(r"cap|limit|grace period|cure period|refund|mutual|written consent|notice",low)),
        "ambiguous":len(re.findall(r"reasonable|appropriate|material|as necessary",low)),
    }

def conflicts(clause,context):
    c=clause.lower(); x=context.lower(); out=[]
    if re.search(r"6\s*month|six\s*month|short.?term",x):
        if re.search(r"12\s*month|one year",c): out.append("Conflicts with your shorter-term plan.")
        if re.search(r"90\s*day|120\s*day",c): out.append("Long notice may reduce your planned flexibility.")
    if re.search(r"budget|student|limited|afford",x) and re.search(r"deposit|penalt|late fee|increase|escalat|amount",c):
        out.append("May materially affect your budget.")
    if re.search(r"privacy|personal data|customer data",x) and re.search(r"share|third party|transfer|sell",c):
        out.append("Deserves extra review because of your privacy priority.")
    if re.search(r"startup|small business|early stage",x) and re.search(r"exclusive|minimum|long.?term|auto.?renew",c):
        out.append("May be restrictive for a flexible business model.")
    return out

def analyze_clause(t,ctx):
    cat=category(t); f=features(t); conf=conflicts(t,ctx)
    score=18+min(f["money"]/10000,18)+min(f["pct"]*.7,12)+min(f["days"]/20,10)+min(f["months"]*1.5,18)
    score+=f["unilateral"]*12+f["auto"]*9+min(f["negative"]*2,12)+min(f["ambiguous"]*2,8)+min(len(conf)*14,28)-min(f["protective"]*2.4,12)
    score+= {"financial":5,"termination":5,"renewal":4,"liability":5,"restrictions":3,"privacy":3,"ip":3,"disputes":2}.get(cat,0)
    score=int(max(5,min(98,round(score))))
    positive=(f["protective"]>f["negative"] and not conf and score<58)
    level="high" if score>=75 else "medium" if score>=50 else "low"
    reasons=[]
    if f["money"]: reasons.append("Financial amount detected")
    if f["pct"]: reasons.append("Percentage change detected")
    if f["days"]: reasons.append("Notice or deadline detected")
    if f["months"]: reasons.append("Duration commitment detected")
    if f["unilateral"]: reasons.append("One-sided discretion detected")
    if f["auto"]: reasons.append("Automatic renewal detected")
    reasons+=conf
    impact="Protective or relatively balanced language detected." if positive else ("This clause conflicts with your stated situation." if conf else ("Potentially significant exposure." if score>=75 else "Worth clarifying before signing." if score>=50 else "Lower detected exposure."))
    return {"title":t[:95],"category":cat,"label":LABELS[cat],"text":t,"evidence":t,"risk":score,"level":level,"positive":positive,"impact":impact,"reasons":reasons[:6],"features":f}

def analyze(text,ctx):
    cs=[analyze_clause(c,ctx) for c in split_clauses(text)]
    risk=round(np.mean([c["risk"] for c in cs])) if cs else 50
    return {"risk":risk,"clauses":cs,"strengths":[c["title"] for c in cs if c["positive"]][:8],"concerns":[c["title"] for c in sorted(cs,key=lambda x:x["risk"],reverse=True) if c["risk"]>=50][:8],
            "obligations":[{"category":c["label"],"timing":f"{c['features']['days']} days" if c["features"]["days"] else f"{c['features']['months']} months" if c["features"]["months"] else "Review before signing","text":c["title"]} for c in cs if c["category"] in {"termination","renewal","financial"}][:15]}

def similarity(a,b):
    v=TfidfVectorizer(stop_words="english").fit_transform([a,b])
    return round(float(cosine_similarity(v[0:1],v[1:2])[0][0])*100,1)

def compare(a,b,ctx,priority):
    aa=analyze(a,ctx); bb=analyze(b,ctx)
    used=set(); diffs=[]
    for ca in aa["clauses"]:
        best=(-1,0)
        for i,cb in enumerate(bb["clauses"]):
            if i in used or ca["category"]!=cb["category"]: continue
            s=similarity(ca["text"],cb["text"])
            if s>best[1]: best=(i,s)
        i,s=best
        if i>=0 and s>=28:
            cb=bb["clauses"][i];used.add(i)
            diffs.append({"type":"same" if s>=92 else "changed","category":ca["label"],"a":ca["text"],"b":cb["text"],"a_risk":ca["risk"],"b_risk":cb["risk"],"similarity":s,"difference":"The clauses cover similar ground but contain different wording or conditions." if s<92 else "No material wording difference detected."})
        else:
            diffs.append({"type":"removed","category":ca["label"],"a":ca["text"],"b":"","a_risk":ca["risk"],"b_risk":None,"similarity":0,"difference":"Present in Contract A; no matching clause was detected in Contract B."})
    for i,cb in enumerate(bb["clauses"]):
        if i not in used: diffs.append({"type":"added","category":cb["label"],"a":"","b":cb["text"],"a_risk":None,"b_risk":cb["risk"],"similarity":0,"difference":"Present in Contract B; no matching clause was detected in Contract A."})
    weights=PRIORITIES.get(priority,PRIORITIES["balanced"])
    def weighted(cs):
        return round(sum(c["risk"]*weights.get(c["category"],.7) for c in cs)/max(1,len(cs)))
    wa,wb=weighted(aa["clauses"]),weighted(bb["clauses"])
    winner="Contract A" if wa<wb-3 else "Contract B" if wb<wa-3 else "Too close to call"
    rec="Contract A" if winner=="Contract A" else "Contract B" if winner=="Contract B" else None
    negotiation=[]
    for d in diffs:
        if d["type"]=="changed":
            hi=max(d["a_risk"] or 0,d["b_risk"] or 0)
            if hi>=60: negotiation.append(f"Review the changed {d['category'].lower()} clause and negotiate clearer or less restrictive terms.")
        elif d["type"]=="added" and (d["b_risk"] or 0)>=60:
            negotiation.append(f"Ask for clarification or protection around the new {d['category'].lower()} clause in Contract B.")
    return {"winner":winner,"best":rec,"score_a":wa,"score_b":wb,"similarity":similarity(a,b),"explanation":("Contract A has lower weighted exposure for the selected priority." if winner=="Contract A" else "Contract B has lower weighted exposure for the selected priority." if winner=="Contract B" else "The scores are close; compare the highlighted trade-offs before choosing."),"a":aa,"b":bb,"differences":diffs[:80],"negotiation":list(dict.fromkeys(negotiation))[:8]}
