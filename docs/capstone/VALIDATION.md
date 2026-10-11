# Validation record — 11 October 2026 (India)

## Confirmed here

- **32 automated tests passed, 0 failed, 0 skipped**, using Python 3.12 and a real temporary PostgreSQL server. The dedicated test database was separate from production and was cleaned up after the run.
- PostgreSQL concurrency checks confirmed that two approvals for one application result in one mocked provider call. OAuth tests confirmed tenant binding, encryption, one-use state and rejection of a different verified sender account.
- Tests also cover profile/job/loop isolation, exact-message approval, daily attempt limits, changed résumé rejection, preserved application status, no retries after uncertain delivery, opted-in scheduled discovery and template validation.
- Additional regression checks cover DOCX table/merged-cell text, Unicode word boundaries, null optional provider descriptions, missing/conflicting location metadata and literal Indian degree evidence without inferring work experience from graduation years.
- Desktop browser checks exercised the New Loop interface and local Share app guidance. Mobile checks exercised navigation and confirmed no horizontal page overflow at 390 px. The screenshot in this directory is an actual local browser render, with no uploaded résumé or applicant identity.
- Read-only Greenhouse discovery for `python` on the Stripe/Figma boards returned **3 India/worldwide-policy listings** and **0 source errors** during this run. An all-location request returned 115 records. These are transient feed results, not submissions or a complete list of vacancies.

## Pending external validation

- The owner supplied https://5dasesqq5hdkocoz5dupwp.streamlit.app/ and reported the setup screen. The cloud workspace's network proxy blocked its request to that domain with a CONNECT 403, so the public website was not independently verified here.
- The reported setup screen identifies missing private sign-in/database configuration. PostgreSQL credentials, Google Web OAuth settings and random cookie/encryption keys must be entered in Streamlit Secrets.
- Real Google consent, two hosted user accounts, persistence after a hosted restart, verified production TLS, intentional user-approved Gmail delivery and the public WhatsApp share flow must be validated after configuration. Provider calls in automated tests are mocked; no real email was sent.
- Daily hosted discovery needs the Actions database secret and the workflow on the repository's default branch. Passing the scheduler tests does not establish that production cron is active.
- Matching accuracy has not been measured on a labeled résumé/job dataset. A heuristic score is not a probability of eligibility or interview success.

## Not implemented

Automatic authorized ATS submission, automatic inbox/reply synchronization, OCR and a trained semantic matching model are not implemented. Employer-page submissions and interview/rejection states require manual completion or confirmation.
