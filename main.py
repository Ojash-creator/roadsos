"""
RoadSoS – Emergency Services Chatbot (Ollama Edition)
======================================================
Road Safety Hackathon 2026 | IIT Madras (CoERS)

Uses Ollama (free, local, no API key needed) for AI.
Model: llama3 (or any model pulled in Ollama)

Install Ollama : https://ollama.com/download
Pull model     : ollama pull llama3
Run server     : uvicorn main:app --port 8000
"""

import os, json, re, math, sqlite3
from typing import Optional
import ollama
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

DB_PATH      = os.path.join(os.path.dirname(__file__), "data", "roadsos.db")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

app = FastAPI(title="RoadSoS API (Ollama)", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel):
    message: str
    latitude:  Optional[float] = None
    longitude: Optional[float] = None
    country_code: Optional[str] = "IN"
    conversation_history: Optional[list] = []

class ChatResponse(BaseModel):
    reply: str
    services: Optional[list] = []
    emergency_numbers: Optional[dict] = None

def get_db():
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; return conn

def haversine(lat1,lon1,lat2,lon2):
    R=6371; p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def find_nearby_services(lat,lon,service_type=None,country_code=None,radius_km=60,limit=5):
    conn=get_db(); q,p="SELECT * FROM emergency_services WHERE 1=1",[]
    if service_type: q+=" AND service_type=?"; p.append(service_type)
    if country_code: q+=" AND country_code=?"; p.append(country_code.upper())
    rows=conn.execute(q,p).fetchall(); conn.close()
    results=[]
    for row in rows:
        d=haversine(lat,lon,float(row["latitude"]),float(row["longitude"]))
        if d<=radius_km:
            r=dict(row); r["distance_km"]=round(d,2); results.append(r)
    results.sort(key=lambda x:x["distance_km"]); return results[:limit]

def get_emergency_numbers(country_code):
    conn=get_db()
    row=conn.execute("SELECT * FROM countries WHERE code=?",(country_code.upper(),)).fetchone()
    conn.close(); return dict(row) if row else {}

def search_by_city(city,service_type=None,country_code=None):
    conn=get_db(); q,p="SELECT * FROM emergency_services WHERE LOWER(city) LIKE ?",[f"%{city.lower()}%"]
    if service_type: q+=" AND service_type=?"; p.append(service_type)
    if country_code: q+=" AND country_code=?"; p.append(country_code.upper())
    rows=conn.execute(q,p).fetchall(); conn.close(); return [dict(r) for r in rows]

INTENT_PATTERNS={
    r"hospital|trauma|clinic|doctor|medical|injury|hurt|bleeding|accident|crash":"hospital",
    r"ambulance|emri|ems|108":"ambulance",
    r"police|pcr|100|station|fir":"police",
    r"tow|towing|breakdown|recovery":"towing",
    r"puncture|tyre|flat|tire":"puncture",
    r"rescue|fire|trapped":"rescue",
}
CITY_RE=re.compile(r"\b(chennai|hyderabad|mumbai|bengaluru|bangalore|delhi|kolkata|pune|new york|london|sydney|singapore)\b",re.IGNORECASE)

def detect_intent(text):
    for pat,stype in INTENT_PATTERNS.items():
        if re.search(pat,text,re.IGNORECASE): return stype
    return None

def fetch_relevant_services(message,lat,lon,country_code):
    service_type=detect_intent(message); services=[]
    if lat and lon:
        services=find_nearby_services(lat,lon,service_type=service_type,country_code=country_code,limit=5)
    else:
        m=CITY_RE.search(message)
        if m: services=search_by_city(m.group(0),service_type=service_type)[:5]
    return services,service_type

def services_to_text(services):
    if not services: return "No services found in database for this location."
    lines=[]
    for s in services:
        dist=f"{s['distance_km']} km away" if s.get("distance_km") else s.get("city","")
        trauma=" [Trauma Centre]" if s.get("has_trauma_centre") else ""
        lines.append(f"- {s['name']} ({s['service_type'].upper()}){trauma}\n  Address: {s.get('address','N/A')}\n  Phone: {s.get('phone','N/A')}{' / '+s['phone_alt'] if s.get('phone_alt') else ''}\n  Distance: {dist}")
    return "\n".join(lines)

SYSTEM_PROMPT="""You are RoadSoS, an emergency services assistant for road accident victims.
- Always lead with the most critical action (call ambulance first)
- Use ONLY the SERVICES DATA provided — never invent phone numbers
- If no services listed, tell user to call 112 immediately
- Keep responses short and clear — this is an emergency
- India emergency numbers: Ambulance=108, Police=100, Fire=101, All=112"""

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    services,_=fetch_relevant_services(req.message,req.latitude,req.longitude,req.country_code or "IN")
    emg=get_emergency_numbers(req.country_code or "IN")
    context=[]
    if req.latitude and req.longitude: context.append(f"GPS: {req.latitude:.4f},{req.longitude:.4f}")
    if emg: context.append(f"Emergency numbers: All={emg.get('emergency_number','112')}, Ambulance={emg.get('ambulance_number','108')}, Police={emg.get('police_number','100')}")
    context.append(f"\nSERVICES DATA:\n{services_to_text(services)}")

    messages=[{"role":"system","content":SYSTEM_PROMPT}]
    for turn in req.conversation_history[-6:]: messages.append(turn)
    messages.append({"role":"user","content":f"{req.message}\n\n[CONTEXT]\n"+"\n".join(context)})

    try:
        resp=ollama.chat(model=OLLAMA_MODEL,messages=messages,options={"temperature":0.3,"num_predict":512})
        reply=resp["message"]["content"]
    except Exception as e:
        reply=("⚠️ AI offline. Nearest services from database:\n\n"+services_to_text(services)+f"\n\n🆘 Call: {emg.get('emergency_number','112')}")

    return ChatResponse(reply=reply,services=services,emergency_numbers=emg)

@app.get("/health")
def health():
    try: ollama.list(); ai=f"Ollama OK ({OLLAMA_MODEL})"
    except: ai="Ollama not running — DB fallback active"
    return {"status":"ok","ai":ai}

@app.get("/emergency/{country_code}")
def emergency_numbers(country_code:str):
    n=get_emergency_numbers(country_code)
    if not n: raise HTTPException(404,f"Country '{country_code}' not found")
    return n

@app.get("/nearby")
def nearby(lat:float,lon:float,type:str=None,country:str="IN",radius:float=50):
    return find_nearby_services(lat,lon,service_type=type,country_code=country,radius_km=radius)

@app.get("/",response_class=HTMLResponse)
def index():
    return open(os.path.join(os.path.dirname(__file__),"static","index.html")).read()

if __name__=="__main__":
    import uvicorn; uvicorn.run("main:app",host="0.0.0.0",port=8000,reload=True)
