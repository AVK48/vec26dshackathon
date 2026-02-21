def get_advice(label: str, opportunity_type: str = "UNKNOWN"):
    label = (label or "").upper()
    opportunity_type = (opportunity_type or "UNKNOWN").upper()

    base = []

    if label == "SAFE":
        base = [
            "Verify the domain spelling and prefer the official careers website.",
            "Do not share OTP/password or bank details on any page."
        ]
    elif label == "SUSPICIOUS":
        base = [
            "Do not enter credentials or personal data on this link.",
            "Verify the opportunity on the company’s official careers page.",
            "If received via WhatsApp/Telegram, ask for official email confirmation."
        ]
    else:  # PHISHING
        base = [
            "Do not proceed. Close the page and do not enter any details.",
            "Block/report the sender and report the link to your college/authorities.",
            "Apply only via official company career portals."
        ]

    # Opportunity-type guidance (student-focused)
    if opportunity_type == "UNPAID":
        base.insert(0, "This appears to be UNPAID. If it’s not aligned with your goals, avoid wasting time.")
    elif opportunity_type == "STIPEND":
        base.insert(0, "This appears to be STIPEND-based. Confirm stipend amount and duration on official sources.")
    elif opportunity_type == "PAID":
        base.insert(0, "This appears to be PAID. Confirm compensation details only on official portals/interview emails.")

    return base




    st.markdown("### ✅ Safer places to apply (verified / reputable)")
    st.write("**Government / official**")
    st.write("• AICTE Internship Portal (official)")  # cite in docs/readme
    st.write("• National Career Service (NCS) (Govt. of India)")  # cite

    st.write("**Popular reputable platforms**")
    st.write("• LinkedIn Jobs")
    st.write("• Naukri")
    st.write("• Indeed")
    st.write("• Glassdoor")
    st.write("• Internshala")