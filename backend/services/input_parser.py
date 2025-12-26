from langdetect import detect
import re

_STOP = {"un","une","le","la","les","à","au","aux","de","du","des","et","en","d","a","the","to","of","y","el","la","los","las","de","del"}

def clean_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9àâäéèêëïîôöùûüçñ\s]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def detect_language(text: str) -> str:
    # si requête trop courte, on force FR
    if len(text.split()) <= 2:
        return "fr"

    try:
        lang = detect(text)
    except:
        return "fr"

    return lang if lang in {"fr", "en", "es", "vi"} else "fr"

def extract_strict_keywords(text: str) -> list[str]:
    toks = [t for t in text.split() if t and t not in _STOP]
    # mini normalisations
    return list(dict.fromkeys(toks))

def expand_keywords(text: str) -> list[str]:
    exp = set([text])

    # relations parent/enfant (FR/EN/ES)
    if any(w in text for w in ["père","pere","father","dad","padre"]):
        exp |= {"père","father","dad","padre","parent","family"}
    if any(w in text for w in ["mère","mere","mother","madre"]):
        exp |= {"mère","mother","madre","parent","family"}
    if any(w in text for w in ["fille","daughter","hija"]):
        exp |= {"fille","daughter","hija","child","enfant"}
    if any(w in text for w in ["fils","son","hijo"]):
        exp |= {"fils","son","hijo","child","enfant"}

    # verbes de message
    if any(w in text for w in ["parle","parler","talk","say","dime","habla"]):
        exp |= {"message","letter","tell","say","talk","dime","carta"}

    return list(exp)

def parse_theme(theme: str) -> dict:
    theme_clean = clean_text(theme)
    lang = detect_language(theme_clean)
    strict = extract_strict_keywords(theme_clean)
    expanded = expand_keywords(theme_clean)
    return {
        "raw": theme,
        "clean": theme_clean,
        "strict_keywords": strict,
        "expanded_keywords": expanded,
        "language": lang
    }
