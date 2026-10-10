# AutoJob AI — multi-user job review and application dashboard

Upload a résumé, review extracted evidence, configure India/remote preferences, discover real vacancies and inspect similarity scores. Confirm mandatory eligibility and an employer-published application contact before preparing an email. Review the exact message and original PDF, then explicitly approve each send.

The Streamlit dashboard supports private OIDC sign-in, tenant-isolated PostgreSQL records, per-user Gmail OAuth with encrypted tokens, daily attempt limits, duplicate-send protection and application tracking. An external scheduled discovery workflow finds jobs for opted-in users; it never sends applications.

**Implemented:** literal résumé evidence, public feeds, review and approval, Gmail transport, tracking and deployment configuration. **Requires external configuration:** public Streamlit deployment, PostgreSQL, Google OIDC/Gmail OAuth and scheduler credentials. **Not implemented:** automatic reply synchronization, OCR, authorized ATS submission integrations. ATS applications use the employer's official page. Similarity scores do not establish eligibility, and user confirmation does not guarantee employer acceptance.

See [deployment and validation instructions](DEPLOYMENT.md). Do not commit credentials, tokens or real résumés. Real delivery and hosted sign-in must be validated after account configuration; mocked tests do not prove them.
