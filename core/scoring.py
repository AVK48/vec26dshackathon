from typing import List, Tuple, Optional


def combine_risk(
    url_score: int,
    site_score: int,
    url_reasons: List[str],
    site_reasons: List[str],
    fee_scam_detected: bool = False,
    fee_evidence: Optional[List[str]] = None
) -> Tuple[int, str, List[str]]:

    fee_evidence = fee_evidence or []

    # Detect if website scan failed/blocked
    site_failed = any(
        ("blocked" in r.lower()) or ("failed" in r.lower()) or ("using url-based" in r.lower())
        for r in site_reasons
    )

    # Base weighting
    if site_failed:
        final_score = int(round(0.85 * url_score + 0.15 * site_score))
    else:
        final_score = int(round(0.60 * url_score + 0.40 * site_score))

    # Hard rule: fee scam signals are extremely suspicious for students
    if fee_scam_detected:
        final_score = max(final_score, 80)

    final_score = max(0, min(100, final_score))

    # Safety rule: high URL score should not show SAFE
    if url_score >= 85 and final_score < 70:
        final_score = 75

    # Label mapping
    if final_score < 35:
        label = "SAFE"
    elif final_score <= 70:
        label = "SUSPICIOUS"
    else:
        label = "PHISHING"

    # Reasons: URL first for clarity, then site, then fee evidence
    reasons = []
    for r in (url_reasons + site_reasons):
        if r and r not in reasons:
            reasons.append(r)

    if fee_scam_detected:
        reasons.insert(0, "Payment/Fee request detected (high scam risk for students).")
        if fee_evidence:
            reasons.insert(1, f"Fee-related keywords: {', '.join(fee_evidence[:6])}.")

    return final_score, label, reasons


def get_advice(label: str, opp_type: str = "UNKNOWN") -> List[str]:
    """
    Returns actionable advice based on the final risk label
    and opportunity type (PAID / STIPEND / UNPAID / UNKNOWN).
    """
    base = {
        "SAFE": [
            "✅ This link appears safe, but always stay alert.",
            "🔍 Verify the company on LinkedIn or Glassdoor before applying.",
            "📧 Use a secondary email for job applications to avoid spam.",
        ],
        "SUSPICIOUS": [
            "⚠️ Proceed with caution — something looks off.",
            "🔍 Search the company name + 'scam' or 'review' on Google.",
            "📞 Try to find and call/email an official contact before sharing personal info.",
            "🚫 Never share Aadhaar, PAN, or bank details upfront.",
        ],
        "PHISHING": [
            "🚨 Do NOT apply or click any links on this page.",
            "🛑 Never enter your password, OTP, or payment info.",
            "📢 Report this URL to cybercrime.gov.in if you're in India.",
            "🗑️ Delete any emails from this source immediately.",
        ],
    }

    extra = []
    if opp_type == "UNPAID":
        extra.append("💼 This appears to be unpaid — ensure you're gaining real skills/experience.")
    elif opp_type == "UNKNOWN":
        extra.append("❓ Compensation is not clearly mentioned — ask before applying.")

    return base.get(label, []) + extra


def format_reasons_for_display(reasons: List[str]) -> str:
    """Formats reason list into a clean numbered string for Streamlit."""
    if not reasons:
        return "No specific issues detected."
    return "\n".join(f"{i+1}. {r}" for i, r in enumerate(reasons))