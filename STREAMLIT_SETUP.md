# Streamlit dashboard for your existing job_agent_mvp

Extract **streamlit_app.py** into `D:\LIBA course\new model\job_agent_mvp` alongside `agent.py`.

In PowerShell:

```powershell
Set-Location 'D:\LIBA course\new model\job_agent_mvp'
& '.\.venv\Scripts\python.exe' -m pip install streamlit pandas
& '.\.venv\Scripts\python.exe' -m streamlit run streamlit_app.py
```

Open http://localhost:8501 if the browser doesn't open automatically.

The UI does not send emails or submit ATS forms. 'Normal run' invokes your existing agent and can make Gmail **drafts** only when that agent is configured for them.

Ensure profile.json contains valid JSON; use the Profile tab to fix it. Dashboard shows logged jobs; Live dry run evaluates public Greenhouse and Lever feeds with your OpenAI API key.
