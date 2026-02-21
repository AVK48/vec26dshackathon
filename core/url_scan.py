from urllib.parse import urlparse
import tldextract

SUSPICIOUS_WORDS = [
    "login", "verify", "update", "secure", "account", "banking",
    "confirm", "password", "credential", "signin", "paypal",
    "free", "lucky", "winner", "click", "offer", "limited"
]

def analyze_url(url: str):
    reasons = []
    score = 0
    raw = (url or "").strip()
    if not raw.startswith(("http://", "https://")):
        raw = "http://" + raw
    parsed = urlparse(raw)
    host = parsed.hostname or ""
    path = parsed.path or ""
    full = raw.lower()

    # 1️⃣ HTTPS check
    if parsed.scheme != "https":
        score += 20
        reasons.append("URL is not using HTTPS.")

    # 2️⃣ Length check
    if len(full) > 75:
        score += 15
        reasons.append("URL is unusually long.")

    # 3️⃣ Multiple hyphens
    if host.count("-") >= 2:
        score += 15
        reasons.append("Domain contains multiple hyphens (common in phishing).")

    # 4️⃣ Suspicious TLD
    suspicious_tlds = ["net", "xyz", "top", "info", "cc"]
    ext = tldextract.extract(host)
    if ext.suffix in suspicious_tlds:
        score += 15
        reasons.append(f"Suspicious top-level domain: .{ext.suffix}")

    # 5️⃣ Brand impersonation check
    brands = ["google", "microsoft", "amazon", "aws", "openai"]
    for brand in brands:
        if brand in host and host != f"{brand}.com":
            score += 25
            reasons.append(f"Possible brand impersonation detected: {brand}")

    # 6️⃣ Suspicious keywords
    hits = [w for w in SUSPICIOUS_WORDS if w in full]
    if hits:
        score += min(20, 5 * len(hits))
        reasons.append(f"Suspicious keywords in URL: {', '.join(hits[:5])}.")

    # 7️⃣ Unusual file extension in path
    if "." in path and not path.endswith((".html", ".php", ".asp", ".aspx")):
        score += 10
        reasons.append("Unusual file extension in URL path.")

    score = max(0, min(100, score))
    return score, reasons


def get_url_verdict(score: int) -> str:
    if score >= 70:
        return "🔴 High Risk — Likely Phishing"
    elif score >= 40:
        return "🟠 Medium Risk — Suspicious"
    elif score >= 20:
        return "🟡 Low Risk — Proceed with Caution"
    else:
        return "🟢 Safe — No major issues detected"