# AutoJob AI — verified-core résumé-to-jobs website

## What this release actually does
- Reads PDF, DOCX and TXT resumes (selectable text PDFs only) and saves them on your PC.
- Queries **Himalayas** and **Remotive** public remote-jobs APIs plus any Greenhouse / Lever employer board tokens you enter.
- Lists jobs with source names, locations, full descriptions, original application links and estimated lexical match scores.
- Filters India/worldwide-labeled jobs. Jobs labeled only `Remote` without eligibility evidence are not automatically accepted in the India + remote filter.
- Saves job records to `data/autojob_website.db`, supports saving status, CSV export.
- Provides separate **LinkedIn / Indeed / Naukri search links**, not scraped postings or misleading "API matches".
- **Does not** send mail, fill ATS forms or auto-apply; job applications take place on the original provider's page.

## Install (Windows PowerShell)
1. Extract ZIP to a separate folder such as `D:\LIBA course\new model\AutoJob_Verified_Release`.
2. Open PowerShell inside the extracted folder.
3. To use the package *without touching your existing project*: `powershell -ExecutionPolicy Bypass -File .\START_WEBSITE.ps1`
4. Open **http://localhost:8502** (not localhost:8501, which may show an unrelated Streamlit server).
5. To upgrade your existing project instead, use:
   `powershell -ExecutionPolicy Bypass -File .\INSTALL_WEBSITE.ps1 -TargetDirectory "D:\LIBA course\new model\job_agent_mvp"`
6. Then run `powershell -ExecutionPolicy Bypass -File "D:\LIBA course\new model\job_agent_mvp\START_WEBSITE.ps1"`

## Verification
`python -m compileall -q .`
`$env:PYTHONPATH='.'; python -m pytest -q`

Live APIs require an internet connection; bad boards may show an error. API feed results are not guaranteed to contain every vacancy. Scores are similarity estimates and not a claim of formal eligibility. PDF scanner images are not supported without OCR. The application does not use the OpenAI API for scoring in this release.

## Source documents
- https://himalayas.app/docs/remote-jobs-api
- https://remotive.com/remote-jobs/api
- https://docs.greenhouse.io/job-board.html
- https://github.com/lever/postings-api
