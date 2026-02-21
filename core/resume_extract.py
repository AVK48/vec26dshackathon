# core/resume_extract.py
from __future__ import annotations

import os
import io
import tempfile
from docx import Document
import PyPDF2


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        stream = io.BytesIO(file_bytes)
        reader = PyPDF2.PdfReader(stream)
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts).strip()
    except Exception:
        return ""


def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        doc = Document(tmp_path)
        os.remove(tmp_path)

        parts = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
        return "\n".join(parts).strip()
    except Exception:
        return ""


def extract_resume_text(uploaded_file) -> str:
    """
    Extract text from uploaded PDF/DOCX.
    If extracted text is too short -> return empty string.
    """
    if uploaded_file is None:
        return ""

    name = (uploaded_file.name or "").lower()
    file_bytes = uploaded_file.getvalue()

    if name.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif name.endswith(".docx"):
        text = extract_text_from_docx(file_bytes)
    else:
        return ""

    if len(text.strip()) < 200:
        return ""
    return text