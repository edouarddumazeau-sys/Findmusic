import numpy as np

def compute_relevance(lyrics: str, strict: list, expanded: list) -> float:
    text = lyrics.lower()
    score = 0

    for w in strict:
        if w in text:
            score += 2

    for w in expanded:
        if w in text:
            score += 1

    if score <= 0:
        return 0.15  # plancher V1

    return min(1.0, score / 20.0)


def compute_density(lyrics: str, strict: list) -> float:
    lines = [l.strip() for l in lyrics.split("\n") if l.strip()]
    if not lines:
        return 0.0

    matches = 0
    for line in lines:
        low = line.lower()
        for w in strict:
            if w in low:
                matches += 1
                break

    return min(1.0, matches / len(lines))


def compute_centrality(lyrics: str, strict: list) -> float:
    lines = [l.strip() for l in lyrics.split("\n") if l.strip()]
    if len(lines) < 8:
        return 0.0

    first = " ".join(lines[:8]).lower()
    mid = " ".join(lines[len(lines)//2: len(lines)//2 + 8]).lower()
    last = " ".join(lines[-8:]).lower()

    score = 0.0
    for segment in [first, mid, last]:
        for w in strict:
            if w in segment:
                score += 0.33
                break

    return min(1.0, score)


def extract_snippet(lyrics: str, strict: list) -> str:
    lines = [l.strip() for l in lyrics.split("\n") if l.strip()]
    if not lines:
        return ""

    scored = []
    for line in lines:
        low = line.lower()
        count = 0
        for w in strict:
            if w in low:
                count += 1
        if count > 0:
            scored.append((count, line))

    if not scored:
        return "\n".join(lines[:2])

    scored.sort(key=lambda x: x[0], reverse=True)
    best = [scored[0][1]]
    if len(scored) > 1:
        best.append(scored[1][1])

    return "\n".join(best)


def classify(density: float, centrality: float) -> str:
    return "main" if (density + centrality) > 0.25 else "secondary"


def weighted_shuffle(items: list) -> list:
    if not items:
        return items

    scores = np.array([max(0.01, float(i["relevance"])) for i in items])
    weights = scores / scores.sum()
    idx = np.random.choice(len(items), size=len(items), replace=False, p=weights)
    return [items[i] for i in idx]


def analyze_songs(songs: list, parsed_theme: dict, max_results: int = 20) -> dict:
    strict = parsed_theme.get("strict_keywords", [])
    expanded = parsed_theme.get("expanded_keywords", [])

    enriched = []

    for s in songs:
        lyrics = s.get("lyrics_processed") or ""
        if not lyrics.strip():
            continue

        rel = compute_relevance(lyrics, strict, expanded)
        den = compute_density(lyrics, strict)
        cen = compute_centrality(lyrics, strict)
        snippet = extract_snippet(lyrics, strict)
        category = classify(den, cen)

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
            "category": category,
            "spotify_link": None
        })

    enriched.sort(key=lambda x: x["relevance"], reverse=True)
    mixed = weighted_shuffle(enriched[:40])

    main = [x for x in mixed if x["category"] == "main"][:max_results]
    secondary = [x for x in mixed if x["category"] == "secondary"][:max_results]

    return {
        "results_main": main,
        "results_secondary": secondary
    }
