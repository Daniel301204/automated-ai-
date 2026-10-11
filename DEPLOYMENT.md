# Streamlit Community Cloud deployment

This is a multi-user review application. It requires OIDC sign-in and durable PostgreSQL storage before accepting uploads. Each user's résumé, settings, jobs and email connection are isolated by their identity-provider user ID. No shared Gmail sender is used. Public job content and matching do not require OpenAI.

## What works, and what still requires setup

- PDF/DOCX/TXT text extraction, literal education/experience evidence and recognized skills; candidate preferences are entered manually. Scanned PDFs require separate OCR.
- Public job feeds with keyword and conservative India/worldwide filtering; source failures are visible. Similarity scores do not prove eligibility. The Netflix example board returned 404 during testing.
- Per-user Gmail OAuth, encrypted refresh-token storage, exact message/PDF approval, mandatory-evidence confirmation and a daily limit of 1–5 attempts, measured in UTC. Gmail acceptance is recorded as awaiting response. A timeout becomes delivery_unknown and cannot be retried in the app.
- External scheduled discovery for opted-in users. The scheduler does not send mail or submit ATS applications.
- Tracking and CSV export. Employer replies/interviews/rejections and external ATS submissions are manually confirmed. Automatic inbox synchronization and authorized ATS submission adapters are not implemented.

Local tests cannot verify actual Google consent, real delivery or the published site. Do those deployment checks after supplying configuration. Never claim an application was submitted from a listing API response.

## Deploy

1. Put the reviewed code in `Daniel301204/automated-ai-` on the branch you intend to deploy. In Streamlit Community Cloud, create an app with entrypoint `streamlit_app.py`. Choose Python 3.12 in Advanced settings. The repository originally used the `project` branch; local changes must be pushed before Cloud can see them.
2. Create a managed PostgreSQL database. Use its connection URL with driver prefix `postgresql+psycopg://`. URL-encode special characters in the password. Use `sslmode=verify-full&sslrootcert=system` with a public CA certificate; for a private CA supply the trusted CA through supported configuration. The app enforces hostname/certificate verification for remote PostgreSQL connections. Use a dedicated database role and enable database backups. Never use ephemeral Cloud disk for real user records.
3. In Google Cloud, configure an OAuth consent screen and an OAuth **Web application** client. Register both exact redirects: `https://YOUR_APP.streamlit.app/oauth2callback` for sign-in, and `https://YOUR_APP.streamlit.app/` for Gmail connection. Enable the Gmail API. Configure your authorized JavaScript origin to the app's HTTPS origin.
4. Paste the structure from `.streamlit/secrets.example.toml` into Community Cloud's Secrets editor, replacing placeholders privately. Do not commit `.streamlit/secrets.toml`. Generate a Fernet key with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` and a cookie secret with `python -c "import secrets; print(secrets.token_urlsafe(48))"` in your own private terminal. Retain the encryption key securely: changing it without migrating tokens requires users to reconnect Gmail.
5. Configure Google's test users while the OAuth app is in testing. Gmail send permission requires Google consent and may require OAuth verification before general public use. Testing-mode offline refresh tokens may expire after seven days. Do not bypass Google's verification requirements.
6. Sign in, upload a résumé, review its evidence and save your details on Personal Info. Create a New Loop with your search preferences, reviewed template and limits. Connect Gmail in Personal Info → Account Settings using the same verified email as sign-in. Each user authorizes their own connection. No Google password is requested by the app.
7. Inspect public feeds, review an actual vacancy and verify the application email using the employer's official page. Download the exact attached PDF and approve the exact message only when you intend to send it. Confirm Gmail Sent and the app's awaiting_response status. This check is a real send; tests use mocks instead.

To invite friends, open **Share app** in the sidebar and copy the public URL or select **Share on WhatsApp**. The URL is derived from the configured HTTPS `auth.redirect_uri` on `*.streamlit.app`; OAuth paths, query parameters and fragments are excluded. WhatsApp opens with the app link ready for your review and sending. For Google OAuth testing, add each friend's email to the allowed test users first. Local preview displays deployment guidance instead of a shareable URL.

## Daily discovery

The included GitHub Actions workflow `.github/workflows/discovery.yml` runs at approximately 03:00 UTC / 08:30 India time, subject to GitHub scheduling delays. Add the same database URL as the repository Actions secret `AUTOJOB_DATABASE_URL`. Scheduled workflows must be present on the repository's default branch; a deployment branch alone does not activate cron. Users must explicitly activate each saved loop in New Loop or My loops. Legacy account-level opt-in is retained only for accounts without saved loops. The workflow can be tested with workflow_dispatch. For many users, replace this serial batch with a dedicated worker and monitored scheduler; the included job has a 30-minute timeout.

Partial source failures preserve successful results and cause the scheduled run to report failure. Review Actions logs. No email approval can be supplied by this workflow.

## Development and validation

Use the existing isolated checkout; do not create a worktree unless requested.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
AUTOJOB_LOCAL_DEV=1 .venv/bin/python -m streamlit run streamlit_app.py --server.address 127.0.0.1
```

Local development uses a SQLite database in ignored `data/`. Real Gmail dispatch requires PostgreSQL. Never set `AUTOJOB_LOCAL_DEV=1` on Community Cloud or an exposed server. Production sign-in fails closed when auth/storage configuration is missing.

For PostgreSQL integration tests, set `AUTOJOB_TEST_POSTGRES_URL` to a dedicated test database and run pytest. The tests create tables and uniquely scoped temporary users, then remove their own rows. Without this variable the PostgreSQL concurrency and OAuth persistence tests are explicitly skipped. CI supplies a PostgreSQL service.

If a process stops after reserving a send, or Gmail times out, reconcile it against Gmail Sent. This app conservatively blocks another send instead of risking duplicate applications. Database administrators should investigate such records; they must not blindly reset the send reservation.

The legacy `agent.py` rejects `ENABLE_AUTO_SEND=1`; approval-gated dashboard dispatch is the supported sending path. Windows Task Scheduler scripts are not needed on Community Cloud.

## Interface changes

The public brand is LoopingCV. New Loop stores real tenant-isolated configurations, not sample loops. My loops supports running, pausing and copying searches. All Matches reranks jobs against the current résumé and applies both loop and account thresholds. My Applications keeps the exact-message approval gate. Personal Info saves first/last name, location and optional phone; the email comes from verified sign-in and is not copied from the reference screenshots.

The supplied screenshots guide appearance, not integrations. Radius/hybrid filtering, AI answering, pricing plans, ATS submission and automatic reply synchronization are not implemented. Their UI explains availability. The Streamlit version is pinned to the version used in browser and application tests to keep widget styling consistent.
