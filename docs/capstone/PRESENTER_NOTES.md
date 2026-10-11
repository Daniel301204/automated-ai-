# LoopingCV: presenter notes

Replace the student and department placeholders on the cover.

## Slide 1: LoopingCV

Introduce LoopingCV as an explainable job-search and application-review prototype. Replace the student and department placeholders. This is not a claim that the public service or every requested integration is already complete.

## Slide 2: Reduce repetitive job-search work

The problem is repetitive discovery, repeated résumé uploads and scattered tracking. The objective is a private workspace that centralizes the workflow while requiring explicit human verification. It does not guarantee that a candidate qualifies or receives interviews.

## Slide 3: From résumé to reviewed application

Explain the six stages. Extraction reads literal evidence and preferences are entered by the user. Listings come from actual public feeds. A match score is only a similarity signal. Gmail transport is implemented but needs configuration; automated ATS form submission is not implemented.

## Slide 4: A private workspace with external integrations

The UI uses Google OIDC for private sign-in. The workflow layer runs extraction, scoring, review and approval checks. PostgreSQL isolates records by a stable identity. Public feeds are read-only. Gmail uses a user's own encrypted refresh token and only sends after a database reservation. The scheduler discovers jobs and never sends applications.

## Slide 5: Explainable keyword matching

Explain the actual implementation: recognized skill overlap contributes 50%, scaled keyword overlap 32% and title overlap 18%. If a job has no recognized skills, keyword overlap substitutes for that component. Scores are clamped to 0–100. These are heuristic similarity scores, not calibrated probabilities. Accuracy has not been measured on a labeled dataset.

## Slide 6: LoopingCV dashboard

This screenshot is an actual browser render of the current local interface. It is not a deployed public website or evidence of a completed job application. Show the New Loop wizard, CV Checker, All Matches, My Applications and Board. Share app becomes useful after a valid public deployment is configured.

## Slide 7: Safeguards around each outgoing email

Discuss why approved sending needs PostgreSQL concurrency protection. Approval fingerprints prevent changing an already-approved message. Per-user locking enforces quotas. Sent or uncertain applications cannot be automatically retried. Remote database TLS is verified and Gmail tokens are encrypted. These safeguards are covered by tests but real delivery still needs a deployed acceptance test.

## Slide 8: 32 automated checks passed

The full suite passed with 32 checks and no skips, including concurrent approvals and encrypted, user-bound, one-use OAuth persistence. Provider sends in the suite are mocked: these tests do not establish real delivery. Browser checks exercised desktop/mobile navigation. Live read-only Greenhouse discovery also returned actual India listings. Model accuracy was not measured.

## Slide 9: Implemented behavior and remaining work

Be candid about status. Résumé extraction, loops, discovery, matching, review and tracking are implemented. Gmail transport and scheduling need external configuration. ATS submission and inbox synchronization are not implemented. Interviews and rejections are manually confirmed. The public deployment needs the user's Streamlit, database and Google accounts.

## Slide 10: Finish configuring the public app

The setup screen means the app code is running but auth/database secrets are missing. Use the actual Streamlit app URL for both Google callbacks. Enter private credentials in Streamlit Secrets. Add demo friends to Google test users while OAuth is in testing. Validate separate accounts and approved Gmail delivery before presenting the integration as live.

## Slide 11: A short, reproducible demonstration

Walk through these six actions. In local mode, sending is disabled and the presentation should show the saved draft and attachment review. Once hosted sign-in, PostgreSQL and per-user Gmail are configured, the owner can approve an intentional real test email and verify Gmail Sent. Do not send applications using fictional demo credentials or a fictional résumé.

## Slide 12: A reliable baseline for further development

Conclude with measurable next steps rather than promising perfection. Publish and validate the authenticated app; evaluate ranking on a labeled dataset; add only authorized ATS provider adapters; implement inbox tracking with the required additional OAuth scopes and consent. The current version is a tested prototype with documented limits.
