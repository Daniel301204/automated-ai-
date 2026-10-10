# Run LoopingCV on your computer

This is the source code for the LoopingCV interface and job review workflow. Local preview stores one development workspace on your computer. Multi-user sign-in and approval-gated Gmail sending are configured separately for Streamlit Community Cloud; see [DEPLOYMENT.md](DEPLOYMENT.md).

## Windows

1. Install **Python 3.12** from [python.org](https://www.python.org/downloads/). Enable the Python launcher during installation.
2. Extract **all** files from the ZIP into a folder you own, such as `Documents\LoopingCV`. Keep the folder structure intact.
3. Double-click **RUN_LOOPINGCV.bat**. The first run installs the dependencies and needs an internet connection. Keep the console window open.
4. Open **http://localhost:8502** in your browser if it does not open automatically.

You can also open PowerShell in the extracted folder and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\START_LOOPINGCV.ps1
```

The execution-policy option applies only to that PowerShell process; it does not change your computer's permanent policy. The launcher needs no administrator access. Press **Ctrl+C** in the console to stop.

## Try the workflow

1. Open **Personal Info** and add your name and location. Open **CV Checker**, upload a selectable-text PDF, DOCX or TXT résumé and review the extracted evidence. Scanned PDFs need OCR, which is not implemented.
2. Open **New Loop**. Enter job titles, choose India/remote preferences and available feeds, then continue through Email Template, Settings and Review. Save the loop.
3. Open **Search Jobs**, select your saved loop and run the search. This requests real public listings and needs internet access. Results depend on feed availability, current vacancies and your query.
4. Review **All Matches**, confirm eligibility and verify an application contact on the employer's official page. Use **My Applications** to inspect a draft when those checks are satisfied. Local preview deliberately disables the send button.
5. Use **Board** and **My Applications** to inspect stored status. A saved draft is not a submitted application.

The current résumé extractor reads literal evidence, and the matcher compares keywords. There is no trained AI model or LLM required for this preview, and no OpenAI API key is needed. A match score is similarity, not proof of eligibility. Generated answers, invented skills and guessed email addresses are not used by this dashboard.

## Run again and edit the code

Your local résumé, loops and jobs persist in `data/development.db`. This file contains private data: keep it on your computer and out of Git. Start the same launcher again to reopen the workspace. To reset the preview, stop the app and remove only that database; doing so deletes the local workspace.

Edit `streamlit_app.py` for page behavior, `looping_ui.py` for styling, `loops.py` for saved searches, and `workflow.py` for storage and approval checks. Save the file and use Streamlit's rerun prompt. Keep email approval checks in place when developing hosted sending.

To run the existing checks from PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Two PostgreSQL integration checks skip without a dedicated test database. These checks do not send real emails. The Windows wrapper has been reviewed; the Python startup path and app have been validated in the Linux cloud environment, not on your laptop.

## macOS or Linux

In the source folder with Python 3.12 installed:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_local.py
```

## If startup fails

- **Python 3.12 missing:** install it, close the console and run the launcher again.
- **Port 8502 already in use:** stop your previous LoopingCV console with Ctrl+C before starting again.
- **Dependency download failed:** check the displayed error and internet connection, then retry.
- **Setup screen instead of the dashboard:** use `RUN_LOOPINGCV.bat` or `run_local.py`; running `streamlit_app.py` directly does not enable local mode.
- **No jobs:** try a broader title and another supported source. Never treat an empty feed or a feed failure as a successful application.

The preview binds to your computer's loopback interface. Use the authenticated PostgreSQL configuration in DEPLOYMENT.md for public hosting; do not expose local development mode to other users.
