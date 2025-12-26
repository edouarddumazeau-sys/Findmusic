from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.input_parser import parse_theme
from services.lyrics_finder import find_lyrics
from services.language_handler import normalize_lyrics
from services.theme_analyzer import analyze_songs

app = FastAPI(title="Appli musique - Backend")

class SearchRequest(BaseModel):
    theme: str
    max_results: int = 20

@app.get("/health")
def health():
    return {"status": "OK"}

@app.post("/search")
def search(req: SearchRequest):
    theme = (req.theme or "").strip()
    if not theme:
        raise HTTPException(status_code=400, detail="theme vide")

    parsed = parse_theme(theme)
    songs_raw = find_lyrics(parsed)
    songs_processed = normalize_lyrics(songs_raw, parsed)
    result = analyze_songs(songs_processed, parsed, max_results=min(req.max_results, 20))

    return {
        "query": parsed["raw"],
        "language_query": parsed["language"],
        **result
    }
    
CACHE = {}  # theme_clean -> (timestamp, response)

@app.post("/search")
def search(req: SearchRequest):
    theme = (req.theme or "").strip()
    parsed = parse_theme(theme)
    key = parsed["clean"]

    import time
    now = time.time()
    if key in CACHE and now - CACHE[key][0] < 3600:
        return CACHE[key][1]

    songs_raw = find_lyrics(parsed)
    songs_processed = normalize_lyrics(songs_raw, parsed)
    result = analyze_songs(songs_processed, parsed, max_results=min(req.max_results, 20))

    payload = {"query": parsed["raw"], "language_query": parsed["language"], **result}
    CACHE[key] = (now, payload)
    return payload
