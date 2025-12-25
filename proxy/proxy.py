import os
import requests
from fastapi import FastAPI, Request, HTTPException

app = FastAPI(title="Appli musique - Proxy")
BACKEND_URL = os.getenv("BACKEND_URL", "").rstrip("/")

@app.get("/health")
def health():
    return {"status": "proxy OK"}

@app.post("/search")
async def search(req: Request):
    if not BACKEND_URL:
        raise HTTPException(status_code=500, detail="BACKEND_URL manquant")
    payload = await req.json()
    r = requests.post(f"{BACKEND_URL}/search", json=payload, timeout=30)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()
