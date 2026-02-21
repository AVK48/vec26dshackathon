# core/resume_match.py
import re
from typing import Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


STOPWORDS = {
    "the","a","an","and","or","to","of","in","on","for","with","as","is","are","was","were",
    "be","been","by","at","from","this","that","it","we","you","they","their","our","your",
    "will","can","should","may","must","not","have","has","had","do","does","did","but",
    # extra filler words (reduces noise)
    "experience","knowledge","skill","skills","responsible","role","work","working","team",
    "ability","strong","good","excellent","required","requirements","preferred"
}

WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.\-]{1,}")


def _clean(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _tokenize_keywords(text: str) -> List[str]:
    # Keep tech tokens like c++, c#, node.js, mlops, etc.
    tokens = [t.lower() for t in WORD_RE.findall(text or "")]
    tokens = [t for t in tokens if len(t) >= 3 and t not in STOPWORDS]
    return tokens


def _terms_with_bigrams(tokens: List[str]) -> List[str]:
    # add bigrams: "machine learning"
    bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
    return tokens + bigrams


def compute_match(resume_text: str, jd_text: str) -> Dict:
    resume_clean = _clean(resume_text)
    jd_clean = _clean(jd_text)

    if len(resume_clean) < 30 or len(jd_clean) < 30:
        return {"match_percent": 0, "missing_keywords": [], "keywords_used": []}

    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        stop_words=list(STOPWORDS)
    )

    try:
        X = vectorizer.fit_transform([resume_clean, jd_clean])
    except ValueError:
        return {"match_percent": 0, "missing_keywords": [], "keywords_used": []}

    sim = cosine_similarity(X[0], X[1])[0][0]
    match_percent = int(round(sim * 100))
    match_percent = max(0, min(100, match_percent))

    # Missing keywords: based on top TF-IDF features from JD
    feature_names = vectorizer.get_feature_names_out()
    jd_vec = X[1].toarray().ravel()
    top_idx = jd_vec.argsort()[::-1]

    resume_tokens = _tokenize_keywords(resume_clean)
    resume_terms = set(_terms_with_bigrams(resume_tokens))

    keywords_used = []
    missing_keywords = []

    for idx in top_idx:
        term = feature_names[idx].strip()
        if not term or len(term) < 3:
            continue
        if term in STOPWORDS:
            continue
        if term in keywords_used:
            continue

        keywords_used.append(term)

        if term not in resume_terms:
            missing_keywords.append(term)

        if len(missing_keywords) >= 12 and len(keywords_used) >= 18:
            break

    return {
        "match_percent": match_percent,
        "missing_keywords": missing_keywords[:12],
        "keywords_used": keywords_used[:18]
    }


def suggestions_from_missing(missing_keywords: List[str]) -> List[str]:
    if not missing_keywords:
        return [
            "Strong alignment. Add 1–2 quantified achievements aligned to the JD.",
            "Mirror the JD wording in your project bullets (tool + impact metric).",
        ]

    return [
        "Add missing keywords only if truthful (Skills/Projects/Experience): " + ", ".join(missing_keywords[:8]),
        "Rewrite bullets using Action + Tool + Result (metric).",
        "Move the most JD-relevant project to the top and highlight matching tech stack.",
    ]