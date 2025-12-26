from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.input_parser import parse_theme
from services.lyrics_finder import find_lyrics
from services.language_handler import normalize_lyrics
from services.theme_analyzer import analyze_songs

app = FastAPI(title="FindMusic - Backend")

class SearchRequest(BaseModel):
    theme: str
    max_results: int = 20

@app.get("/health")
def health():
    return {"status": "OK"}

import os

@app.get("/debug_env")
def debug_env():
    tok = os.getenv("GENIUS_TOKEN", "")
    return {"genius_token_present": bool(tok and tok.strip()), "genius_token_len": len(tok.strip())}
    
@app.post("/search")
def search(req: SearchRequest):
    theme = (req.theme or "").strip()
    if not theme:
        raise HTTPException(status_code=400, detail="theme vide")

    # 1) Parse
    parsed = parse_theme(theme)

    # 2) Récupération paroles
    songs_raw, lf_debug = find_lyrics(parsed)

    # 3) Normalisation / langues
    songs_processed = normalize_lyrics(songs_raw, parsed)

    # 4) Analyse thème
    result = analyze_songs(
        songs_processed,
        parsed,
        max_results=min(int(req.max_results), 20)
    )

    # 5) Réponse + debug
    return {
        "query": parsed["raw"],
        "language_query": parsed.get("language", "en"),
        "debug": {
            "songs_raw_count": len(songs_raw),
            "songs_processed_count": len(songs_processed),
            "main_count": len(result.get("results_main", [])),
            "secondary_count": len(result.get("results_secondary", [])),
            "lyrics_finder": lf_debug
        },
        **result
    }
