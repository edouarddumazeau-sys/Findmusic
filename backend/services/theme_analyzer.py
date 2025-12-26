import numpy as np

def compute_relevance(lyrics: str, strict: list[str], expanded: list[str]) -> float:
    t = lyrics.lower()
    score = 0
    for w in strict:
        if w in t:
            score += 2
    for w in expanded:
        if w in t:
            score += 1
    return min(1.0, score / 20.0)

def compute_density(lyrics: str, strict: list[str]) -> float:
    lines = [l.strip() for l in lyrics.split("\n") if l.strip()]
    keys = list(set(strict + expanded))
    if not lines:
        return 0.0
    hit = 0
    for line in lines:
        low = line.lower()
        if any(w in low for w in keys):
            hit += 1
    return min(1.0, hit / len(lines))

def compute_centrality(lyrics: str, strict: list[str]) -> float:
    lines = [l.strip() for l in lyrics.split("\n") if l.strip()]
    if len(lines) < 8:
        return 0.0
    first = " ".join(lines[:8]).lower()
    mid = " ".join(lines[len(lines)//2: len(lines)//2 + 8]).lower()
    last = " ".join(lines[-8:]).lower()
    score = 0.0
    for seg, w in [(first, 0.45), (mid, 0.20), (last, 0.35)]:
        if any(k in seg for k in strict):
            score += w
    return min(1.0, score)

def extract_snippet(lyrics: str, strict: list[str]) -> str:
    lines = [l.strip() for l in lyrics.split("\n") if l.strip()]
    if not lines:
        return ""

    scored = []
    for line in lines:
        low = line.lower()
        s = sum(1 for w in strict if w in low)
        if s > 0:
            scored.append((s, line))

    # ✅ Si rien ne match strictement, on prend un fallback lisible
    if not scored:
        return "\n".join(lines[:2])  # 2 premières lignes non vides

    scored.sort(key=lambda x: x[0], reverse=True)
    best = [scored[0][1]]
    if len(scored) > 1:
        best.append(scored[1][1])
    return "\n".join(best)

def classify(density: float, centrality: float) -> str:
    return "main" if (density + centrality) > 0.35 else "secondary"

def weighted_shuffle(items: list[dict]) -> list[dict]:
    if not items:
        return items
    scores = np.array([max(0.01, float(x["relevance"])) for x in items])
    weights = scores / scores.sum()
    idx = np.random.choice(len(items), size=len(items), replace=False, p=weights)
    return [items[i] for i in idx]

def analyze_songs(songs: list, parsed_theme: dict, max_results: int = 20) -> dict:
    strict = parsed_theme["strict_keywords"]
    expanded = parsed_theme["expanded_keywords"]

    enriched = []
    for s in songs:
        lyr = s.get("lyrics_processed") or ""
        if not lyr.strip():
            continue
        rel = compute_relevance(lyr, strict, expanded)
        if rel == 0:
            rel = 0.15  # plancher V1 pour éviter zéro résultat
        den = compute_density(lyr, strict)
        cen = compute_centrality(lyr, strict)
        snippet = extract_snippet(lyr, strict)
        cat = classify(den, cen)

    if rel < 0.1:
    continue
        enriched.append({
            "title": s.get("title"),
            "artist": s.get("artist"),
            "year": s.get("year"),
            "language_original": s.get("language_original"),
            "translation_used": s.get("translation_used", False),
            "relevance": rel,
            "density": den,
            "centrality": cen,
            "snippet": snippet,
            "category": cat,
            "spotify_link": None
        })

    enriched.sort(key=lambda x: x["relevance"], reverse=True)
    mixed = weighted_shuffle(enriched[:40])

    main = [x for x in mixed if x["category"] == "main"][:max_results]
    sec = [x for x in mixed if x["category"] == "secondary"][:max_results]
    return {"results_main": main, "results_secondary": sec}
