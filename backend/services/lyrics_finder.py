import os
import requests
from bs4 import BeautifulSoup
import time

GENIUS_TOKEN = os.getenv("GENIUS_TOKEN", "").strip()
GENIUS_SEARCH = "https://api.genius.com/search"

def _scrape_lyrics_from_genius_page(url: str) -> str | None:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, timeout=15)
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    containers = soup.select('div[data-lyrics-container="true"]')
    if not containers:
        # fallback older pages
        legacy = soup.select_one("div.lyrics")
        if legacy:
            return legacy.get_text("\n").strip()
        return None
    text = "\n".join([c.get_text("\n") for c in containers]).strip()
    return text if text else None

def _search_genius(keyword: str, limit_hits: int = 10) -> list[dict]:
    headers = {"User-Agent": "Mozilla/5.0"}
    if not GENIUS_TOKEN:
        return []
    headers = {"Authorization": f"Bearer {GENIUS_TOKEN}"}
    r = requests.get(GENIUS_SEARCH, headers=headers, params={"q": keyword}, timeout=15)
    if r.status_code == 429:
        time.sleep(15)
        return []
  #  if r.status_code != 200:
  #      return []
    if r.status_code != 200:
    # on remonte l'info pour debug en logs Render
        print("GENIUS status:", r.status_code, "body:", r.text[:200])
        return []
    hits = r.json().get("response", {}).get("hits", [])[:limit_hits]
    out = []
    for h in hits:
        res = h.get("result", {})
        out.append({
            "title": res.get("title"),
            "artist": (res.get("primary_artist") or {}).get("name"),
            "url": res.get("url"),
            "year": None,  # on enrichira plus tard
        })
    return [x for x in out if x["title"] and x["artist"] and x["url"]]

def _lyrics_ovh(artist: str, title: str) -> str | None:
    url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return None
        lyr = r.json().get("lyrics")
        return lyr.strip() if lyr else None
    except:
        return None

def find_lyrics(parsed_theme: dict) -> list[dict]:
    keywords = parsed_theme["expanded_keywords"][:2]
    keywords = keywords[:5]
    songs: list[dict] = []

    # 1) Genius (prioritaire)
    for kw in keywords:
        for cand in _search_genius(kw, limit_hits=3):
            lyrics = _scrape_lyrics_from_genius_page(cand["url"])
            if lyrics:
                songs.append({
                    "title": cand["title"],
                    "artist": cand["artist"],
                    "year": cand["year"],
                    "lyrics": lyrics
                })
        time.sleep(0.25)
        if len(songs) >= 12:
            break

    # 2) Fallback lyrics.ovh (si Genius vide ou pauvre)
    if len(songs) < 15:
        # on tente sur quelques combinaisons simples (title/artist déjà trouvés si on en a)
        # sinon on ne peut pas “chercher” efficacement via lyrics.ovh
        pass

    # dédoublonnage
    uniq = {}
    for s in songs:
        key = (s["artist"].lower(), s["title"].lower())
        uniq[key] = s
    return list(uniq.values())[:12]
