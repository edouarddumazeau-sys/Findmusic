# backend/services/lyrics_finder.py

import os
import time
import requests
from bs4 import BeautifulSoup

GENIUS_SEARCH = "https://api.genius.com/search"
GENIUS_TOKEN = os.getenv("GENIUS_TOKEN", "").strip()

# User-Agent mobile réaliste (réduit les blocages "bot" côté pages Genius)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                  "Version/17.0 Mobile/15E148 Safari/604.1"
}


def _lyrics_ovh(artist: str, title: str) -> str | None:
    url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        lyr = r.json().get("lyrics")
        return lyr.strip() if lyr else None
    except Exception:
        return None


def _scrape_lyrics_from_genius_page(url: str) -> str | None:
    """
    Scrape lyrics sur les pages Genius (le token API ne fournit pas les paroles).
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        # Nouveau format Genius
        containers = soup.select('div[data-lyrics-container="true"]')
        if containers:
            text = "\n".join([c.get_text("\n") for c in containers]).strip()
            return text if text else None

        # Ancien format
        legacy = soup.select_one("div.lyrics")
        if legacy:
            text = legacy.get_text("\n").strip()
            return text if text else None

        return None

    except Exception:
        return None


def _search_genius_debug(keyword: str, limit_hits: int = 10):
    """
    Retourne (candidats, status)
    status = "200" / "401" / "429" / "no_token" / "exc:..."
    """
    if not GENIUS_TOKEN:
        return [], "no_token"

    auth_headers = {"Authorization": f"Bearer {GENIUS_TOKEN}"}

    try:
        r = requests.get(
            GENIUS_SEARCH,
            headers={**auth_headers, **HEADERS},
            params={"q": keyword},
            timeout=15
        )
    except Exception as e:
        return [], f"exc:{type(e).__name__}"

    if r.status_code == 429:
        time.sleep(15)
        return [], "429"

    if r.status_code != 200:
        return [], str(r.status_code)

    data = r.json()
    hits = data.get("response", {}).get("hits", [])[:limit_hits]

    out = []
    for h in hits:
        res = h.get("result", {})
        out.append({
            "title": res.get("title"),
            "artist": (res.get("primary_artist") or {}).get("name"),
            "url": res.get("url"),
            "year": None,
        })

    out = [x for x in out if x.get("title") and x.get("artist") and x.get("url")]
    return out, "200"


def find_lyrics(parsed_theme: dict):
    """
    Retourne (songs_out, debug)
    songs_out: list[dict] avec title/artist/year/lyrics
    debug: dict pour savoir exactement où ça bloque
    """
    keywords = (parsed_theme.get("expanded_keywords") or [])[:2]

    debug = {
        "keywords_used": keywords,
        "genius_search_statuses": [],
        "genius_hits_total": 0,
        "scrape_ok": 0,
        "scrape_fail": 0,
        "ovh_ok": 0,
        "ovh_fail": 0,
        "added_songs": 0,
    }

    songs: list[dict] = []

    for kw in keywords:
        cands, status = _search_genius_debug(kw, limit_hits=6)
        debug["genius_search_statuses"].append({kw: status})
        debug["genius_hits_total"] += len(cands)

        for cand in cands:
            lyrics = _scrape_lyrics_from_genius_page(cand["url"])
            if lyrics:
                debug["scrape_ok"] += 1
            else:
                debug["scrape_fail"] += 1
                lyrics = _lyrics_ovh(cand["artist"], cand["title"])
                if lyrics:
                    debug["ovh_ok"] += 1
                else:
                    debug["ovh_fail"] += 1

            if lyrics:
                songs.append({
                    "title": cand["title"],
                    "artist": cand["artist"],
                    "year": cand.get("year"),
                    "lyrics": lyrics
                })

            if len(songs) >= 25:
                break

        if len(songs) >= 25:
            break

        time.sleep(0.25)  # petite pause entre keywords

    # dédoublonnage
    uniq = {}
    for s in songs:
        key = (s["artist"].lower(), s["title"].lower())
        uniq[key] = s

    songs_out = list(uniq.values())[:25]
    debug["added_songs"] = len(songs_out)

    return songs_out, debug
