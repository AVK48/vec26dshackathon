import streamlit as st

from core.url_scan import analyze_url
from core.website_scan import scan_website
from core.oppurtunity import detect_fee_scam_signals, classify_opportunity_type
from core.scoring import combine_risk
from core.advice import get_advice

# ✅ Resume module
from core.resume_extract import extract_resume_text
from core.resume_match import compute_match, suggestions_from_missing

# ✅ NEW: Website briefing module
from core.site_brief import brief_website


st.set_page_config(
    page_title="SecureApplyAI",
    page_icon="🛡️",
    layout="centered"
)

st.title("🛡️ SecureApplyAI")
st.caption("Protect yourself from fake internships, phishing links & job scams.")
st.markdown("---")

tab1, tab2 = st.tabs(["🛡️ Scam Check", "📄 Resume Intelligence"])


# ──────────────────────────────────────────────────────────────────────────────
# TAB 1: Scam Check
# ──────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("### Paste the Job / Internship URL")
    url = st.text_input(
        label="URL",
        placeholder="e.g. https://internship-apply.xyz/register",
        label_visibility="collapsed",
        key="scam_url"
    )

    st.markdown("### Paste the Job Description or Message *(optional)*")
    msg = st.text_area(
        label="Message",
        placeholder="Paste the recruiter message, email body, or JD here...",
        height=160,
        label_visibility="collapsed",
        key="scam_msg"
    )

    run_scan = st.button("🔍 Analyze Now", use_container_width=True, key="run_scam")
    st.markdown("---")

    if run_scan:
        if not url or not url.strip():
            st.error("Please paste a URL to analyze.")
        else:
            # -------------------------
            # Core scan + risk scoring
            # -------------------------
            with st.spinner("Visiting URL and analyzing signals..."):
                url_score, url_reasons = analyze_url(url)
                site_score, site_reasons, site_meta = scan_website(url)

                combined_text = (site_meta.get("extracted_text", "") + "\n" + (msg or "")).strip()

                fee_detected, fee_evidence = detect_fee_scam_signals(combined_text)
                opp = classify_opportunity_type(combined_text)

                final_score, label, reasons = combine_risk(
                    url_score=url_score,
                    site_score=site_score,
                    url_reasons=url_reasons,
                    site_reasons=site_reasons,
                    fee_scam_detected=fee_detected,
                    fee_evidence=fee_evidence
                )

                advice = get_advice(label, opp["type"])

            # -------------------------
            # Result header
            # -------------------------
            label_color = {"SAFE": "green", "SUSPICIOUS": "orange", "PHISHING": "red"}
            color = label_color.get(label, "gray")
            st.markdown(
                f"### Result: <span style='color:{color}'><b>{label}</b></span>",
                unsafe_allow_html=True
            )
            st.metric("Risk Score", f"{final_score} / 100")
            st.markdown("---")

            # -------------------------
            # NEW: Website Briefing
            # -------------------------
            st.markdown("### 🧾 Website Briefing")
            try:
                with st.spinner("Generating website briefing..."):
                    site_brief = brief_website(url, crawl_pages=3)

                st.write(f"**Pages scanned:** {site_brief['pages_scanned']}")
                st.write(f"**Final URL:** {site_brief['meta'].get('final_url','')}")
                st.write(f"**Title:** {site_brief['titles'][0] if site_brief['titles'] else 'N/A'}")

                if site_brief["emails"]:
                    st.write("**Emails found:** " + ", ".join(site_brief["emails"]))
                if site_brief["phones"]:
                    st.write("**Phones found:** " + ", ".join(site_brief["phones"]))

                st.write(
                    "**Payment keywords:** " +
                    (", ".join(site_brief["payment_hits"]) if site_brief["payment_hits"] else "None")
                )
                st.write(
                    "**Scam-style keywords:** " +
                    (", ".join(site_brief["scam_hits"]) if site_brief["scam_hits"] else "None")
                )

                st.markdown("**Social signals**")
                st.json(site_brief["socials"])

                with st.expander("Preview of extracted text"):
                    st.write(site_brief["sample_text"])

            except Exception:
                st.warning("Could not generate full website briefing (site blocked scraping or timed out).")

            st.markdown("---")

            # -------------------------
            # Opportunity type
            # -------------------------
            st.markdown("### 💼 Opportunity Type")
            st.write(f"**{opp['type']}**")
            if opp["evidence"]:
                st.caption("Evidence keywords found: " + ", ".join(opp["evidence"][:6]))
            else:
                st.caption("No clear stipend/salary keywords found on page or message.")

            st.markdown("---")

            # -------------------------
            # Why section
            # -------------------------
            st.markdown("#### 🔎 Why this result?")
            for r in reasons[:6]:
                st.write(f"• {r}")

            st.markdown("---")

            # -------------------------
            # Advice section
            # -------------------------
            st.markdown("#### 💡 What should you do?")
            for a in advice:
                st.write(a)

            st.markdown("---")

            # -------------------------
            # Suggested genuine portals
            # -------------------------
            st.markdown("### ✅ Safer places to apply (legal / genuine)")
            st.write("**Government / official**")
            st.write("• AICTE Internship Portal (official)")
            st.write("• National Career Service (NCS) – Govt. of India")

            st.write("**Popular reputable platforms**")
            st.write("• LinkedIn Jobs")
            st.write("• Naukri")
            st.write("• Indeed")
            st.write("• Glassdoor")
            st.write("• Internshala")

            st.markdown("---")

            # -------------------------
            # Transparency expander (existing)
            # -------------------------
            with st.expander("🔬 Show website snippet used for analysis (demo transparency)"):
                st.write(f"**Page Title:** {site_meta.get('title', 'N/A')}")
                snippet = site_meta.get("extracted_text", "")
                st.code(snippet[:1200] + ("..." if len(snippet) > 1200 else ""))


# ──────────────────────────────────────────────────────────────────────────────
# TAB 2: Resume Intelligence
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### Upload your Resume (PDF / DOCX)")
    resume_file = st.file_uploader(
        "Upload Resume",
        type=["pdf", "docx"],
        label_visibility="collapsed",
        key="resume_upload"
    )

    st.markdown("### Paste the Job Description")
    jd_text = st.text_area(
        "Job Description",
        placeholder="Paste the Job Description (JD) here...",
        height=180,
        label_visibility="collapsed",
        key="jd_text"
    )

    run_match = st.button("✅ Check Match", use_container_width=True, key="run_match")
    st.markdown("---")

    if run_match:
        if resume_file is None:
            st.error("Please upload a resume (PDF/DOCX).")
        elif not jd_text or not jd_text.strip():
            st.error("Please paste the Job Description (JD).")
        else:
            with st.spinner("Extracting resume and computing match..."):
                resume_text = extract_resume_text(resume_file)

                if not resume_text:
                    st.error("Could not extract enough text from the resume. Try a clearer PDF/DOCX.")
                else:
                    result = compute_match(resume_text, jd_text)
                    match_percent = result["match_percent"]
                    missing = result["missing_keywords"]

                    st.markdown("### 🎯 Match Score")
                    st.metric("Match %", f"{match_percent} / 100")
                    st.progress(match_percent / 100)

                    st.markdown("---")
                    st.markdown("### 🧩 Missing Keywords")
                    if missing:
                        for kw in missing[:18]:
                            st.write(f"• {kw}")
                    else:
                        st.success("No major missing keywords found (strong alignment).")

                    st.markdown("---")
                    st.markdown("### ✍️ Suggestions")
                    for s in suggestions_from_missing(missing):
                        st.write(f"• {s}")

                    st.markdown("---")
                    st.markdown("### 👀 Extracted Resume Preview")
                    st.code(resume_text[:300] + ("..." if len(resume_text) > 300 else ""))

st.markdown("---")
st.caption("Built with ❤️ for students | SecureApplyAI © 2025")