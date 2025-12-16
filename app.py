import os
import zipfile
from io import BytesIO
from pathlib import Path

import streamlit as st
import PyPDF2
from docx import Document
from langchain_google_genai import ChatGoogleGenerativeAI

# ===============================
# GOOGLE API KEY (Hardcoded)
# ===============================
os.environ["GOOGLE_API_KEY"] = "Paste your GOOGLE_API_KEY"

# ===============================
# STREAMLIT CONFIG
# ===============================
st.set_page_config(
    page_title="Portfolio Website Generator",
    layout="wide"
)

st.title("Portfolio Website Generator")
st.write(
    "Upload your resume to generate a simple, responsive portfolio website "
    "using standard HTML, CSS, and JavaScript."
)

# ===============================
# FILE UPLOAD
# ===============================
resume_file = st.file_uploader(
    "Resume file (PDF or DOCX)",
    type=["pdf", "docx"]
)

# ===============================
# RESUME TEXT EXTRACTION
# ===============================
def extract_text_from_pdf(file) -> str:
    text = ""
    with BytesIO(file.read()) as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text.strip()


def extract_text_from_docx(file) -> str:
    doc = Document(file)
    return "\n".join(p.text for p in doc.paragraphs).strip()

# ===============================
# LLM GENERATION
# ===============================
def generate_portfolio_code(resume_text: str) -> str:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0.25
    )

    system_prompt = """
You are converting resume information into a personal portfolio website.

Guidelines:
- Use clear, practical language
- Keep section titles simple
- Avoid marketing buzzwords
- Write clean, readable code
- No unnecessary animations

Output only code in this format:

--html--
HTML
--html--

--css--
CSS
--css--

--js--
JS
--js--
"""

    user_prompt = f"""
Convert the following resume into a personal portfolio website.

Include:
- Header with name and role
- About section
- Skills
- Work experience
- Projects
- Education
- Contact information

Resume:
{resume_text}
"""

    response = llm.invoke(
        [
            ("system", system_prompt),
            ("user", user_prompt)
        ]
    )

    return response.content

# ===============================
# SAVE + ZIP FILES
# ===============================
def save_and_zip_website(response_text: str) -> str:
    html = response_text.split("--html--")[1]
    css = response_text.split("--css--")[1]
    js = response_text.split("--js--")[1]

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    with open("style.css", "w", encoding="utf-8") as f:
        f.write(css)

    with open("script.js", "w", encoding="utf-8") as f:
        f.write(js)

    zip_name = "portfolio_website.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write("index.html")
        zipf.write("style.css")
        zipf.write("script.js")

    return zip_name

# ===============================
# UI LAYOUT
# ===============================
left, right = st.columns([2, 1])

with left:
    if st.button("Generate website", use_container_width=True):

        if not resume_file:
            st.warning("Please upload a resume file.")
            st.stop()

        ext = Path(resume_file.name).suffix.lower()

        if ext == ".pdf":
            resume_text = extract_text_from_pdf(resume_file)
        elif ext == ".docx":
            resume_text = extract_text_from_docx(resume_file)
        else:
            st.error("Unsupported file format.")
            st.stop()

        st.subheader("Resume Preview")
        st.text_area("", resume_text, height=240)

        with st.spinner("Processing resume..."):
            result = generate_portfolio_code(resume_text)
            save_and_zip_website(result)

        st.success("Website files generated successfully!")

with right:
    if os.path.exists("portfolio_website.zip"):
        st.download_button(
            "Download website files",
            data=open("portfolio_website.zip", "rb"),
            file_name="portfolio_website.zip",
            use_container_width=True
        )

st.markdown("---")
st.caption("Internal tool for generating static portfolio websites")
