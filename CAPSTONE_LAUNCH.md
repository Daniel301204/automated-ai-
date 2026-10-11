# LoopingCV: capstone demo and public deployment

The current project is a working, explainable prototype. It is not a trained language model. It extracts literal résumé evidence, compares skills/keywords, discovers actual listings and prepares user-reviewed applications. Tests demonstrate specific behaviors; they do not establish matching accuracy or guarantee a bug-free service.

**Your public app URL:** https://5dasesqq5hdkocoz5dupwp.streamlit.app/ — created by the owner; private sign-in and database configuration remain pending. The setup page is a configuration gate, not a completed workflow demo.

## What you need to do to get a shareable link

1. Open [Streamlit Community Cloud](https://share.streamlit.io/), connect GitHub and create an app. Select repository **Daniel301204/automated-ai-**, branch **codex/approval-gated-streamlit**, main file **streamlit_app.py**, and **Python 3.12**. Choose the available app address you want. Streamlit assigns the actual HTTPS URL; no public deployment has been created by this workspace. Share that public URL in the chat so the next configuration can use the right redirects.
2. Create a managed PostgreSQL database, for example through [Neon](https://console.neon.tech/). Keep the connection string private. The app requires `postgresql+psycopg://` and verified TLS; see DEPLOYMENT.md for the URL format. Database credentials go in Streamlit Secrets, not chat, Git or PowerShell source files.
3. In [Google Cloud Console](https://console.cloud.google.com/), create an OAuth Web application client and enable the Gmail API. Register **both** `https://YOUR_ACTUAL_APP.streamlit.app/oauth2callback` and `https://YOUR_ACTUAL_APP.streamlit.app/`. Set the authorized origin to the same HTTPS app origin. Configure the consent screen and add yourself and demo friends as test users while it is in testing.
4. In your Streamlit app settings, copy [.streamlit/secrets.example.toml](.streamlit/secrets.example.toml) into the private **Secrets** editor. Replace all placeholders with your actual database, Google and encryption settings. Generate the two private random keys on your computer with the commands below. Save the secrets and restart the app. Leave local development mode disabled on the public app.
5. Open the public URL. Check sign-in, résumé persistence after a restart and isolation between two test accounts. Each account connects its own Gmail in **Personal Info → Account Settings**. Review the exact message, contact evidence and PDF before approving any real email. Check Gmail Sent and the application's awaiting_response status. These live deployment checks are still pending.
6. Open **Share app → Share on WhatsApp** to invite friends. The shared link contains only the public app address. For daily discovery, add the same PostgreSQL URL privately as the GitHub Actions secret `AUTOJOB_DATABASE_URL` and ensure the discovery workflow is on the repository's default branch. The schedule is approximately **08:30 India time**, subject to GitHub scheduling delays; discovery never sends an application.

Generate the encryption key and cookie secret in PowerShell, from the source folder after running the Windows launcher:

```powershell
.\.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste each output only into the corresponding private Streamlit Secrets field. Keep the encryption key stable; changing it without a migration makes existing Gmail tokens unreadable.

## Demo the current workflow

1. Run **RUN_LOOPINGCV.bat** for a local preview, or use your configured public app.
2. Upload a text-readable PDF, DOCX or TXT résumé on **CV Checker**; review the extracted lines and skills. Preferences and eligibility are confirmed by the user.
3. Add your name on **Personal Info**. Create a **New Loop** with India/remote preferences, supported sources, a reviewed email template, threshold and daily limits.
4. Use **Search Jobs**. Verify an actual listing on the original employer page; inspect matched and missing skills in **All Matches**. The score measures text similarity, not eligibility or interview likelihood.
5. Upload a reviewed PDF before preparing email. In **My Applications**, supply the employer-published contact and evidence URL, confirm mandatory requirements and review the exact draft and attachment. Local preview disables sending. Real sending requires authenticated hosted mode, PostgreSQL and the user's Gmail connection.
6. Inspect **Board** and CSV export. Gmail acceptance is recorded automatically; interview/rejection states and external ATS submissions need manual confirmation.

## Feature boundaries for the capstone

| Requested feature | Current implementation |
|---|---|
| Upload once and profile evidence | Implemented; selectable-text PDF, DOCX including tables, TXT; literal skills/education/experience evidence; manual preferences |
| India/remote loops and limits | Implemented; threshold 80–100%, daily attempts 1–5, independent per-user loops |
| Real discovery and matching | Implemented; public feeds, explainable lexical scoring, conservative location review, partial feed error reporting |
| Scheduled agent | Code and tests implemented; requires Actions database secret and workflow on the default branch |
| Personalized résumé emails | Implemented approval and transport; real Google consent/delivery require deployment configuration and live validation |
| ATS website submission | Manual employer-page route; no automatic authorized ATS adapter implemented |
| Application tracking | Automatic dispatch state; manual confirmations for interview/rejection and external submissions; no reply synchronization |
| WhatsApp app-link sharing | Implemented; becomes shareable after the public URL is configured |
| OCR / trained semantic AI model | Not implemented; current matcher uses keywords, without an LLM API key |

Adding automatic ATS submission requires choosing a provider with a supported application API and obtaining the authorized integration credentials. Automatic inbox tracking requires a separate Gmail read integration and corresponding user consent. These are further development tasks, not features implied by passing the current tests.

## Presentation

The simple 12-slide presentation is in [docs/capstone/LoopingCV_Capstone.pptx](docs/capstone/LoopingCV_Capstone.pptx), with a PDF copy and presenter notes. Replace the student/department placeholders on the cover. The slides distinguish implemented behavior, integration setup and future work. Do not describe the automated test count as model accuracy.

For a reproducible, clearly labeled synthetic matching output, run `.venv/bin/python docs/capstone/demo_model.py` (Windows: `.\.venv\Scripts\python.exe docs\capstone\demo_model.py`). It reads the fictional demo résumé and uses the actual extraction/matching code, without contacting an employer or sending an application. The generated [demo_output.json](docs/capstone/demo_output.json) is an illustration, not a real vacancy or an accuracy evaluation.
