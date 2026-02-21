import re
from typing import Dict, List, Tuple

PAID_WORDS = [
    "paid internship", "paid", "salary", "ctc", "package", "compensation",
    "per month", "/month", "monthly", "lpa", "lakh", "stipend"
]
STIPEND_WORDS = [
    "stipend", "stipend based", "stipend-based", "stipend :", "stipend -",
    "₹", "rs", "inr", "per month", "/month"
]
UNPAID_WORDS = [
    "unpaid", "no stipend", "without stipend", "volunteer", "volunteering",
    "no pay", "not paid"
]
FEE_SCAM_WORDS = [
    "registration fee", "processing fee", "training fee", "security deposit",
    "deposit", "pay to confirm", "pay to register", "pay now", "payment required",
    "fees required", "fee required", "pay ₹", "pay rs", "pay inr", "upi", "scan to pay"
]


def _normalize(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_fee_scam_signals(text: str) -> Tuple[bool, List[str]]:
    """Returns (fee_scam_detected, evidence_keywords)."""
    t = _normalize(text)
    hits = []
    for kw in FEE_SCAM_WORDS:
        if kw in t:
            hits.append(kw)
    return (len(hits) > 0), hits[:6]


def classify_opportunity_type(text: str) -> Dict:
    """
    Classify as Paid / Stipend / Unpaid / Unknown based on visible text.
    Returns a dict with type + evidence.
    """
    t = _normalize(text)
    evidence = []

    # Strong unpaid signals first (avoid false "paid" from random ₹ symbols)
    unpaid_hits = [kw for kw in UNPAID_WORDS if kw in t]
    if unpaid_hits:
        return {"type": "UNPAID", "evidence": unpaid_hits[:6]}

    # Stipend signals
    stipend_hits = [kw for kw in STIPEND_WORDS if kw in t]
    if stipend_hits:
        return {"type": "STIPEND", "evidence": stipend_hits[:6]}

    # Paid signals
    paid_hits = [kw for kw in PAID_WORDS if kw in t]
    if paid_hits:
        return {"type": "PAID", "evidence": paid_hits[:6]}

    return {"type": "UNKNOWN", "evidence": evidence}


def get_opportunity_label(result: Dict) -> str:
    """Returns a colored emoji label for display in Streamlit."""
    labels = {
        "PAID":     "💰 Paid Opportunity",
        "STIPEND":  "💵 Stipend-Based",
        "UNPAID":   "⚠️ Unpaid / Volunteer",
        "UNKNOWN":  "❓ Compensation Not Mentioned"
    }
    return labels.get(result["type"], "❓ Unknown")


def compute_overall_risk(url_score: int, fee_scam: bool, opp_type: str) -> Tuple[int, str]:
    """
    Combines URL risk score + fee scam signal + opportunity type
    into a single overall risk score and verdict.
    """
    risk = url_score  # base from URL analysis

    if fee_scam:
        risk += 40  # fee scam is a strong red flag

    if opp_type == "UNPAID":
        risk += 10
    elif opp_type == "UNKNOWN":
        risk += 5

    risk = max(0, min(100, risk))

    if risk >= 70:
        verdict = "🔴 High Risk — Do NOT apply without thorough verification"
    elif risk >= 40:
        verdict = "🟠 Medium Risk — Proceed cautiously"
    elif risk >= 20:
        verdict = "🟡 Low Risk — Looks mostly okay, stay alert"
    else:
        verdict = "🟢 Safe — Opportunity appears legitimate"

    return risk, verdict