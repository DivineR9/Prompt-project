# Lecture Notes to Study Pack — SCSE4041 Milestone 2 (C2)

Simple Streamlit starter prototype. It accepts PDF, DOCX, TXT or pasted lecture notes; extracts text; calls Gemini through **three separate prompts** (content analysis, study notes, practice questions); and allows the study pack to be downloaded as Markdown.

**Status:** Code has been drafted, but the app's Gemini API integration has NOT been tested with your account. Run it, record actual results, and update the report before making any completion claims.

## Run on Windows

1. Download/extract this ZIP. Install Python if needed.
2. Open the extracted folder in File Explorer, click the address bar, type `cmd`, press Enter.
3. Install packages:

   ```bat
   py -m pip install -r requirements.txt
   ```

4. Start the app:

   ```bat
   py -m streamlit run app.py
   ```

5. Open the local URL shown (typically `http://localhost:8501`).
6. Create a Gemini API key at https://aistudio.google.com/apikey. **Never put the key in code, screenshots, or a public repository.**
7. Enter your key into the **sidebar** password field, upload `sample_notes/machine_learning.txt`, select a model ID available to your account, first click **Test Gemini connection (quick check)**, then **Generate study pack**.
8. Check **Content analysis**, **Study notes**, **Practice questions**, and **Download complete study pack**. Save actual screenshots and test outcomes.

## Deploy to a public Streamlit URL

1. Create a **public** GitHub repository and upload the project files (not your API key).
2. Go to https://share.streamlit.io/ and deploy the GitHub repository, selecting `app.py` as the main file.
3. In the Streamlit app's **Secrets**, configure:

   ```toml
   GEMINI_API_KEY = "YOUR_KEY_HERE"
   ```

4. Reboot or rerun your deployed app; test the public URL from a second browser or incognito window.
5. Put the real, working deployed URL into your Milestone 2 report and Form Q11. Do **not** insert a guessed or untested link.

For help with Streamlit deployment and secrets, see:
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management

## Technical notes

- **Inputs:** PDF with selectable text, DOCX, TXT, or manually pasted notes.
- **Three separate Gemini calls:** `P1` analyzes topics, `P2` creates revision notes, `P3` generates practice questions.
- **Output:** three results in tabs and a downloadable `.md` study pack.
- **Current AI model:** `gemini-3.5-flash-lite` is the default for faster, lighter testing; users can change it in the sidebar. The **actual model used** is the one successfully requested during testing.
- **Known limitations:** scanned PDFs unsupported (no OCR), 8 MB upload limit, 65,000-character input limit, large documents not chunked, complex formatting may not be perfectly extracted, Gemini API may require access/quota, generated answers can contain mistakes.

## Evidence needed for the Milestone 2 report

Your PDF **must reflect the real app**, not planned features. After testing:

- Screenshot: uploaded source / text and settings
- Screenshot: produced study notes (actual successful run)
- Screenshot: generated questions and answers (actual successful run)
- Save a test log with at least 10 **executed** tests (the CSV in `docs/` is only a plan, not results)
- Record the actual prompt versions and iteration results
- Make a 90–150-second demo using the actual working app
- Update status for every module and link to the real working prototype/repo

## Folder overview

- `app.py` — Streamlit UI, file extraction, 3 AI prompts, downloads
- `requirements.txt` — Python packages
- `sample_notes/machine_learning.txt` — sample test notes
- `docs/test_plan.csv` — testing plan; **NOT completed test results**
- `CHANGELOG.md` — initial project file log

## Troubleshooting a stuck Step 1/3

- **Step 1/3** means the model call is waiting. A 1 KB TXT file is small; the Gemini network call is the probable bottleneck.
- Use the **Test Gemini connection** button before creating a study pack; it makes one tiny request with a 20-second HTTP timeout.
- Default model is now `gemini-3.5-flash-lite`, which Google currently lists as a fast model. You can still enter another available model in the sidebar.
- Main requests each have a 45-second HTTP timeout; there are three **sequential** requests, so total can still exceed 45 seconds.
- `503` usually means temporary server overload; `429` usually means quota/rate-limit; `401/403` often concerns credentials/permissions; `404` may indicate model access/name. Check the **exact** error before concluding.
- Stop the current app in Command Prompt with Ctrl+C, restart using `py -m streamlit run app.py`, and rerun tests.
- Do not post your API key in screenshots, terminals, source code, or GitHub. Revoke a key if it has been exposed.

**Verification:** This patch was syntax-checked, but no live Gemini API request was possible in the editing environment. The connection test on your computer is the real verification.
