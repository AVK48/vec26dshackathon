# core/site_brief.py
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{8,}\d)")
PAYMENT_WORDS = {"fee", "payment", "pay", "registration fee", "deposit", "upi", "account", "charges"}
SCAM_WORDS = {"whatsapp", "telegram", "limited seats", "pay now", "urgent", "guaranteed", "offer letter", "certificate"}


def _safe_get(url: str, timeout: int = 10, max_bytes: int = 1_500_000) -> tuple[str, dict]:
    headers = {"User-Agent": "SecureApplyAI/1.0 (+student-safety)"}
    resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    meta = {
        "final_url": resp.url,
        "status_code": resp.status_code,
        "redirects": [r.url for r in resp.history] if resp.history else [],
        "content_type": resp.headers.get("content-type", ""),
    }
    content = resp.content[:max_bytes]
    return content.decode(errors="ignore"), meta


def _extract_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    links = []
    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        if not href:
            continue
        full = urljoin(base_url, href)
        links.append(full)
    return links


def _same_domain(url: str, root: str) -> bool:
    return urlparse(url).netloc == urlparse(root).netloc


def brief_website(url: str, crawl_pages: int = 3) -> dict:
    """
    Crawl up to N same-domain pages (including the landing URL) and extract:
    title, key text, contacts, socials, red-flag keywords, external links summary.
    """
    visited = set()
    to_visit = [url]
    texts = []
    all_links = []
    emails = set()
    phones = set()
    titles = []

    meta_first = {}

    while to_visit and len(visited) < crawl_pages:
        u = to_visit.pop(0)
        if u in visited:
            continue
        visited.add(u)

        html, meta = _safe_get(u)
        if not meta_first:
            meta_first = meta

        soup = BeautifulSoup(html, "html.parser")

        t = (soup.title.get_text(" ", strip=True) if soup.title else "")
        if t:
            titles.append(t)

        # remove junk
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        page_text = soup.get_text(" ", strip=True)
        page_text = re.sub(r"\s+", " ", page_text)
        texts.append(page_text[:8000])  # cap per page

        # contacts
        for e in EMAIL_RE.findall(page_text):
            emails.add(e)
        for p in PHONE_RE.findall(page_text):
            phones.add(p)

        links = _extract_links(soup, meta.get("final_url", u))
        all_links.extend(links)

        # crawl a few internal links
        for link in links:
            if _same_domain(link, url) and link not in visited and len(to_visit) < 10:
                to_visit.append(link)

    combined = " ".join(texts).lower()

    payment_hits = sorted({w for w in PAYMENT_WORDS if w in combined})
    scam_hits = sorted({w for w in SCAM_WORDS if w in combined})

    # socials / messaging
    socials = {
        "whatsapp": any("wa.me" in l or "whatsapp.com" in l for l in all_links),
        "telegram": any("t.me" in l or "telegram.me" in l for l in all_links),
        "instagram": any("instagram.com" in l for l in all_links),
        "linkedin": any("linkedin.com" in l for l in all_links),
    }

    externals = [l for l in all_links if urlparse(l).netloc and not _same_domain(l, url)]
    externals = list(dict.fromkeys(externals))[:15]

    return {
        "meta": meta_first,
        "titles": titles[:3],
        "emails": sorted(list(emails))[:8],
        "phones": sorted(list(phones))[:8],
        "payment_hits": payment_hits,
        "scam_hits": scam_hits,
        "socials": socials,
        "external_links": externals,
        "sample_text": " ".join(texts)[:1500],
        "pages_scanned": len(visited),
    }