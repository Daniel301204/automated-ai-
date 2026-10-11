# LoopingCV — multi-user job review and application dashboard

Upload a résumé, review extracted evidence, configure India/remote preferences, discover real vacancies and inspect similarity scores. Confirm mandatory eligibility and an employer-published application contact before preparing an email. Review the exact message and original PDF, then explicitly approve each send.

The Streamlit dashboard supports private OIDC sign-in, tenant-isolated PostgreSQL records, per-user Gmail OAuth with encrypted tokens, daily attempt limits, duplicate-send protection and application tracking. An external scheduled discovery workflow finds jobs for opted-in users; it never sends applications.

**Implemented:** literal résumé evidence, public feeds, review and approval, Gmail transport, tracking and deployment configuration. **Requires external configuration:** public Streamlit deployment, PostgreSQL, Google OIDC/Gmail OAuth and scheduler credentials. **Not implemented:** automatic reply synchronization, OCR, authorized ATS submission integrations. ATS applications use the employer's official page. Similarity scores do not establish eligibility, and user confirmation does not guarantee employer acceptance.

See [deployment and validation instructions](DEPLOYMENT.md). Do not commit credentials, tokens or real résumés. Real delivery and hosted sign-in must be validated after account configuration; mocked tests do not prove them.

For the capstone demonstration, public hosting steps, current feature boundaries and presentation, see [CAPSTONE_LAUNCH.md](CAPSTONE_LAUNCH.md).

Before hosted sign-in and PostgreSQL are configured, the app displays a public demo with shipped fictional résumé/job examples and an interactive keyword matcher. It accepts no uploads, opens no private database and cannot send emails. Owner setup instructions remain available in an expander. Once both required settings are present, the private sign-in flow resumes.

For private hosting configuration on Windows, run `CONFIGURE_STREAMLIT.bat` after creating your PostgreSQL database and Google OAuth Web client. It prepares the secrets locally and copies them for you to paste into Streamlit's private Secrets editor. It preserves existing settings and never prints database/client secret values.

To view and develop the dashboard on your own computer, follow [LOCAL_RUN.md](LOCAL_RUN.md). On Windows, install Python 3.12, extract the source and run `RUN_LOOPINGCV.bat`. The launcher opens a local workspace with email sending disabled.

## LoopingCV interface

The dashboard follows the supplied LoopCV screenshots: a white sidebar, blue controls, light workspace, Personal Info tabs and a four-step New Loop wizard (Search Info → Email Template → Settings → Review). Saved loops contain actual per-user searches, source choices, templates and limits. Radius/hybrid filters, billing and automatic answering are visibly unavailable rather than simulated.

Desktop previews use unsaved example data:

- [New Loop](docs/ui/new-loop.png)
- [Personal Info](docs/ui/personal-info.png)

The existing `AUTOJOB_` development variables and `autojob_` database table names are retained for compatibility. Never enable local development mode on a public host.

After Community Cloud deployment, **Share app** in the sidebar offers a copyable public URL and a **Share on WhatsApp** link. It uses the configured sign-in redirect's public origin, with no résumé or OAuth details in the shared link. Each friend signs in separately. Local preview instead explains how to publish; it cannot provide a public localhost link.
