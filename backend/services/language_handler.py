from langdetect import detect

SUPPORTED = {"fr","en","es","vi"}

def detect_lyrics_language(text: str) -> str:
    try:
        lang = detect(text)
    except:
        return "en"
    return lang if lang in SUPPORTED else "en"

def normalize_lyrics(songs: list, parsed_theme: dict) -> list:
    """
    V1: on marque la langue. Traduction VI sera ajoutée en V1.1 (choix technique).
    On garde la structure dès maintenant pour plugger la traduction sans refactor.
    """
    out = []
    for s in songs:
        lyr = s.get("lyrics") or ""
        if not lyr.strip():
            continue
        lang = detect_lyrics_language(lyr)
        s["language_original"] = lang
        s["translation_used"] = False
        s["lyrics_processed"] = lyr
        out.append(s)
    return out
