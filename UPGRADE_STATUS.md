# AutoJob guarded upgrade — Stage 1

Source inspected from your uploaded ZIP, target folder: `D:\LIBA course\AutoJob_Verified_Release`.

**Implemented:** preserves original Streamlit job search and resume upload; adds Guarded applications page; 80% similarity minimum plus separate human-verified mandatory requirements and original resume checks; candidate-verified recipient mapping; produces a PDF composed of literal lines extracted from original resume; local SQLite review queue; duplicate queue keys. No real send or ATS submission is initiated from the new page.

**Not implemented or unverified:** automatic email delivery, candidate confirmation email, authorized ATS submit API, daily 5-send enforcement against a live Gmail/ATS log, AI factual resume rewriting, live browser smoke test. Existing agent CLI auto-send features are separate and not modified by this stage. Do not enable them yet.

## Windows PowerShell

1. Unzip into a separate folder (not over your existing project).
2. In PowerShell, `Set-Location` to the extracted folder containing `INSTALL_TO_EXISTING.ps1`.
3. `powershell -ExecutionPolicy Bypass -File .\INSTALL_TO_EXISTING.ps1 -TargetDirectory 'D:\LIBA course\AutoJob_Verified_Release'`
4. `Set-Location 'D:\LIBA course\AutoJob_Verified_Release'`
5. `& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt` (if venv missing, create one with `py -3 -m venv .venv`).
6. `& '.\.venv\Scripts\python.exe' -m streamlit run streamlit_app.py --server.port 8504`

If 8504 is occupied, use another port. Navigate to the Guarded applications page. Search jobs, then expand Prepare tailored application for a result scoring at least 80%. Explicitly verify the job's mandatory requirements before proceeding. No emails will be sent.

## Tests

26 pytest tests passed locally including 5 newly introduced for eligibility gates, evidence-only tailoring, PDF, verified email and queue idempotency. Live external API calls and Streamlit browser rendering not tested in this environment.
