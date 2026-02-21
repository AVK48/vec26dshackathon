from typing import List, Tuple, Dict
import requests
from bs4 import BeautifulSoup

KEYWORDS = ["login", "verify", "otp", "password", "bank", "urgent", "account", "payment"]
BRANDS = ["google", "microsoft", "amazon", "aws", "openai"]

def scan_website(url: str) -> Tuple[int, List[str], Dict]:
    """
    Lightweight HTML scan (no JS rendering). Returns:
    (site_score, reasons, meta)
    meta includes extracted_text (truncated) and title.
    """
    reasons = []
    score = 0
    raw = (url or "").strip()
    if not raw.startswith(("http://", "https://")):
        raw = "http://" + raw

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(raw, timeout=6, headers=headers, allow_redirects=True)
        html = resp.text or ""
    except Exception:
        return 0, ["Website content fetch blocked/failed; using URL-based risk signals."], {
            "title": "",
            "extracted_text": ""
        }

    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")
    title_l = title.lower()

    # Visible text
    text = soup.get_text(" ", strip=True)
    text_l = text.lower()

    # Form detection
    forms = soup.find_all("form")
    if forms:
        score += 25
        reasons.append("Website contains a form (possible credential capture).")

    # Password field detection
    if soup.find("input", {"type": "password"}):
        score += 30
        reasons.append("Website contains a password field.")

    # Keyword scan
    kw_hits = [k for k in KEYWORDS if k in text_l]
    if kw_hits:
        score += min(25, 5 * len(kw_hits))
        reasons.append(f"Risky keywords found on page: {', '.join(kw_hits[:6])}.")

    # Brand terms hint
    brand_hits = [b for b in BRANDS if b in text_l or b in title_l]
    if brand_hits:
        score += 10
        reasons.append(f"Brand terms found (possible impersonation): {', '.join(brand_hits[:4])}.")

    score = max(0, min(100, score))

    # Keep a short snippet (helps opportunity type classification + judge demo)
    snippet = text.strip()
    if len(snippet) > 2500:
        snippet = snippet[:2500] + "..."

    return score, reasons, {
        "title": title,
        "extracted_text": snippet
    }


def combine_scan_scores(url_score: int, site_score: int) -> int:
    """
    Weighted combination of URL analysis + website content scan.
    URL scan is slightly more reliable (works even when site blocks scraping).
    """
    combined = int((url_score * 0.5) + (site_score * 0.5))
    return max(0, min(100, combined))


def get_site_verdict(score: int) -> str:
    if score >= 70:
        return "🔴 High Risk — Website shows strong phishing signals"
    elif score >= 40:
        return "🟠 Medium Risk — Website has suspicious elements"
    elif score >= 20:
        return "🟡 Low Risk — Minor concerns detected"
    else:
        return "🟢 Safe — No major red flags on the website"