# AutoJob AI 2.0 — Windows / Streamlit

## Outcome previews
1. Website: profile editor, job sources, application controls.
2. Real public job discovery: Greenhouse and Lever listings filtered to India / remote; no scraping.
3. AI matching: required-qualification eligibility and suitability score.
4. Routing: one verified recruiter email or official ATS review URL.
5. Execution: Gmail drafts or optional guarded Gmail sending only after explicit opt-in. Public ATS listing APIs **do not** authorize submission; no live ATS adapter is bundled.
6. Operations: SQLite and CSV, daily Windows task, no duplicates for sent/drafted jobs.

## Safe installation
Extract ZIP to a new directory. Open PowerShell in the extracted `job_agent_mvp` folder:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\safe_install.ps1 -TargetDirectory 'D:\LIBA course\new model\job_agent_mvp'
Set-Location 'D:\LIBA course\new model\job_agent_mvp'
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
& '.\.venv\Scripts\python.exe' -m pytest -q
& '.\.venv\Scripts\python.exe' agent.py --offline-demo
& '.\.venv\Scripts\python.exe' -m streamlit run streamlit_app.py
```

If no .venv exists, create one with `py -3 -m venv .venv` first. To try live job matching, configure `.env`, `profile.json`, and `boards.json` then run `agent.py --dry-run`. Only run without dry-run after OAuth/contacts review.

### Limitations
ATS submission: **not supplied** without employer-authorized integration and valid integration credentials. Resume PDF upload stores the file but does not automatically extract qualifications; verify `profile.json`. Recruiting replies are not automatically synchronized. Live integrations have not been tested with your accounts. Streamlit is local; background execution relies on Windows Task Scheduler.

**Security**: backups may include credentials; keep them private. Never commit `.env` or OAuth tokens to source control. Never run tests in live-send mode.

## Stage 2: Live Job Discovery — implemented
The dashboard now has a **Live Job Discovery** page. Click **Fetch live vacancies now** to call
public Greenhouse/Lever GET APIs and write `data/discovered_jobs.csv` and
`data/discovery_report.json`. This action requires no OpenAI API key, Gmail OAuth,
or sender authorization. It **never** sends applications. The results are limited
to employer boards listed in `boards.json`, not the entire internet. The India +
remote location filter is a search heuristic: remote jobs may have additional
work-authorization or country restrictions that must be checked during matching.

From PowerShell, independently run:

```powershell
Set-Location 'D:\LIBA course\new model\job_agent_mvp'
& '.\.venv\Scripts\python.exe' agent.py --discover-only
& '.\.venv\Scripts\python.exe' -m streamlit run streamlit_app.py
```

The upgrade installer copies the new `job_discovery.py` module. The existing
`.env`, OAuth files, profile, contacts and database are preserved.
