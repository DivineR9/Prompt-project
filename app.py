"""Lecture Notes to Study Pack — SCSE4041 C2 Milestone 2 starter prototype.

This is application source code, not a claim of successful execution. Run with
`streamlit run app.py` after installing dependencies and configuring an API key.
"""

import io
import os
from datetime import datetime

import fitz
import streamlit as st
from docx import Document
from google import genai
from google.genai import types


MAX_BYTES = 8 * 1024 * 1024
MAX_TEXT_CHARS = 65_000
DEFAULT_MODEL = "gemini-3.5-flash-lite"
API_TIMEOUT_MS = 45_000
TEST_TIMEOUT_MS = 20_000


def get_api_key() -> str:
    """Read a secret without printing or exposing it."""
    from_environment = os.environ.get("GEMINI_API_KEY", "")
    if from_environment:
        return from_environment
    try:
        return str(st.secrets.get("GEMINI_API_KEY", ""))
    except (FileNotFoundError, KeyError, AttributeError):
        return ""


def extract_text(data: bytes, extension: str) -> str:
    """Extract selectable text; scanned PDF OCR is intentionally out of scope."""
    if len(data) > MAX_BYTES:
        raise ValueError("File is too large. Upload a file smaller than 8 MB.")
    if extension == "txt":
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError:
            return data.decode("utf-8-sig", errors="replace")
    if extension == "pdf":
        with fitz.open(stream=data, filetype="pdf") as document:
            if document.is_encrypted:
                raise ValueError("Password-protected PDFs are not supported.")
            return "\n\n".join(page.get_text(sort=True) for page in document)
    if extension == "docx":
        document = Document(io.BytesIO(data))
        paragraphs = [p.text for p in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                paragraphs.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(paragraphs)
    raise ValueError("Unsupported format. Please upload a PDF, DOCX or TXT file.")


def call_model(client: genai.Client, model: str, instruction: str) -> str:
    response = client.models.generate_content(
        model=model,
        contents=instruction,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=2200,
        ),
    )
    text = (getattr(response, "text", None) or "").strip()
    if not text:
        raise RuntimeError("The AI model did not return any text for this step.")
    return text


def make_prompt_1(subject: str, lecture_content: str) -> str:
    return f"""You are an academic content analyst. Analyze the lecture content below.
Use ONLY the supplied lecture text. Identify the main topics, subtopics,
important definitions, key concepts, technical terms and formulas (if present).
Preserve the meaning and technical terms. If any part is missing, unclear or
contradictory, explicitly mention it. Do not invent details.

Subject: {subject}

Lecture content:\n<lecture_notes>\n{lecture_content}\n</lecture_notes>

Output headings:
1. Main topics and subtopics
2. Important definitions
3. Key concepts and technical terms
4. Formulas (if present)
5. Missing or unclear parts
"""


def make_prompt_2(subject: str, difficulty: str, analyzed_content: str) -> str:
    return f"""You are a helpful academic tutor. Create study notes from the
analyzed material below. Use simple, clear language for a college student,
without changing technical meaning. Do not invent unsupported claims.
Keep additional illustrative examples clearly labeled and only include them
if they are directly supported by the supplied analysis.

Subject: {subject}
Difficulty level: {difficulty}

Analyzed content:\n<analysis>\n{analyzed_content}\n</analysis>

Use these headings:
1. Chapter overview
2. Topic-wise study notes
3. Important definitions
4. Key revision points
5. Formulas / steps from the source (if any)
6. Quick revision summary
If information is unavailable, say so rather than guessing.
"""


def make_prompt_3(subject: str, difficulty: str, count: int, study_content: str) -> str:
    mcq_count = max(1, round(count * 0.7))
    short_count = count - mcq_count
    return f"""You are making a practice set from the study notes below.
Use ONLY the provided study content. Generate exactly {count} questions:
{mcq_count} multiple-choice questions with four options each (A-D), and
{short_count} short-answer questions. For each question, give the correct
answer and a brief explanation supported by the notes. Avoid duplicate,
ambiguous and unsupported questions. If the notes are insufficient, explain
this limitation rather than inventing questions.

Subject: {subject}
Difficulty level: {difficulty}
Study notes:\n<study_notes>\n{study_content}\n</study_notes>
"""


st.set_page_config(page_title="Lecture Notes to Study Pack", page_icon="📘", layout="wide")
st.title("📘 Lecture Notes to Study Pack")
st.caption("SCSE4041 • C2 • Student prototype | PDF / DOCX / TXT → Analysis → Study notes → Questions")

with st.sidebar:
    st.header("Settings")
    subject = st.text_input("Subject", value="Computer Science")
    difficulty = st.selectbox("Difficulty level", ["Beginner", "Intermediate", "Advanced"], index=1)
    num_questions = st.slider("Total practice questions", min_value=5, max_value=20, value=10)
    model = st.text_input("Gemini model ID", value=DEFAULT_MODEL,
                          help="Use a model available to your Gemini API key.")
    api_key = st.text_input("Gemini API key (optional if configured as a secret)",
                            value="", type="password", help="Never upload this key to GitHub.")
    st.caption("A key entered here is only used for this session. You can also set GEMINI_API_KEY as an environment variable or a Streamlit secret.")

uploaded_file = st.file_uploader("Upload lecture notes", type=["pdf", "docx", "txt"],
                                 help="Text-based PDFs work; image-only scans need OCR (not included).")
pasted_notes = st.text_area("Or paste a short set of lecture notes", height=130,
                             placeholder="Paste some lecture notes here if you don't have a file...")

# First verify that a tiny API request works, without processing a lecture file.
if st.button("Test Gemini connection (quick check)", use_container_width=True):
    active_key = api_key.strip() or get_api_key()
    if not active_key:
        st.error("Please enter a Gemini API key first.")
    elif not model.strip():
        st.error("Please enter a Gemini model ID first.")
    else:
        try:
            with st.spinner("Checking Gemini API with a short request (up to ~20 seconds)..."):
                with genai.Client(
                    api_key=active_key,
                    http_options=types.HttpOptions(timeout=TEST_TIMEOUT_MS),
                ) as client:
                    reply = client.models.generate_content(
                        model=model.strip(),
                        contents="Reply in one word: OK",
                        config=types.GenerateContentConfig(max_output_tokens=40),
                    )
            if (getattr(reply, "text", None) or "").strip():
                st.success("Gemini API responded! You can now try Generate study pack.")
            else:
                st.warning("Gemini replied but returned no text. Try another available model.")
        except Exception as exc:
            st.error(f"Gemini connection test failed: {type(exc).__name__}: {exc}")
            st.info("Try gemini-3.5-flash-lite. Check key, API quota and network. A 503 usually means temporary service overload.")

if st.button("Generate study pack", type="primary", use_container_width=True):
    if not subject.strip() or not model.strip():
        st.error("Please enter a subject and Gemini model ID.")
        st.stop()

    text = pasted_notes.strip()
    if uploaded_file is not None and not text:
        try:
            extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
            text = extract_text(uploaded_file.getvalue(), extension).strip()
        except Exception as exc:
            st.error(f"Could not read the file: {exc}")
            st.stop()
    if not text:
        st.warning("Please upload a readable file or paste lecture text first.")
        st.stop()
    if len(text) > MAX_TEXT_CHARS:
        st.error(f"The extracted text contains {len(text):,} characters, which is too long for this demo. Please upload a shorter document (max {MAX_TEXT_CHARS:,} characters).")
        st.stop()

    active_key = api_key.strip() or get_api_key()
    if not active_key:
        st.error("A Gemini API key is needed to generate AI study material. Add it in the sidebar or configure GEMINI_API_KEY in Streamlit secrets.")
        st.stop()

    try:
        with genai.Client(
            api_key=active_key,
            http_options=types.HttpOptions(timeout=API_TIMEOUT_MS),
        ) as client:
            with st.spinner("Step 1/3: Identifying main topics..."):
                analysis = call_model(client, model.strip(), make_prompt_1(subject, text))
            with st.spinner("Step 2/3: Creating study notes..."):
                study_notes = call_model(client, model.strip(), make_prompt_2(subject, difficulty, analysis))
            with st.spinner("Step 3/3: Preparing practice questions..."):
                questions = call_model(client, model.strip(), make_prompt_3(subject, difficulty, num_questions, study_notes))
        st.session_state.study_pack = {
            "analysis": analysis,
            "study_notes": study_notes,
            "questions": questions,
            "subject": subject,
            "model": model.strip(),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "input_length": len(text),
        }
    except Exception as exc:
        st.error(f"AI generation failed: {type(exc).__name__}: {exc}")
        st.info("The API request failed. Try the quick connection test, switch to gemini-3.5-flash-lite, and check API quotas / network. A 503 usually means temporary server overload.")
        st.stop()

if "study_pack" in st.session_state:
    result = st.session_state.study_pack
    st.success("Study pack generated. Check the notes and answers against the original material.")
    st.caption(f"Subject: {result['subject']} | Model requested: {result['model']} | Text length: {result['input_length']:,} characters | Generated: {result['generated_at']}")
    tab1, tab2, tab3 = st.tabs(["Content analysis", "Study notes", "Practice questions"])
    with tab1:
        st.markdown(result["analysis"])
    with tab2:
        st.markdown(result["study_notes"])
    with tab3:
        st.markdown(result["questions"])
    combined = (
        f"# Lecture Notes to Study Pack\n\nSubject: {result['subject']}\n"
        f"Model requested: {result['model']}\n\n"
        f"## Content Analysis\n{result['analysis']}\n\n"
        f"## Study Notes\n{result['study_notes']}\n\n"
        f"## Practice Questions\n{result['questions']}\n"
    )
    st.download_button("Download complete study pack (.md)", data=combined,
                       file_name="study_pack.md", mime="text/markdown")

st.divider()
st.caption("Limitations: requires a working Gemini API key and network; scanned/image-only PDFs do not have OCR; text extraction from complex layouts may be imperfect; AI results may contain mistakes. Test before submitting the project.")
