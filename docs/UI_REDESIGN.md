# LoopingCV local interface update

The user approved a full redesign with the LoopingCV name and the existing job search, matching and email approval behavior. Their Overview, New Loop and Personal Info screenshots guide the design. No access to the reference site's authenticated pages was assumed.

The shared shell uses a white sidebar with a full-width selected row, a white top bar, a light gray workspace, blue pill actions and outlined fields. Overview now opens first and contains four setup actions, a greeting with the India date, and five activity cards. The account button displays the saved profile name. The sidebar follows navigation from both the top bar and checklist.

The checklist opens working profile, question-answer, loop and résumé pages. Résumé upload replaces the reference browser-extension action because no extension is available. No pricing, extension, AI answering, ATS submission or reply synchronization feature is invented to imitate the reference.

My loops shows actual saved configurations and activation state. Search Jobs and All Matches use vacancy cards with current scores, matched skills, original employer links and saved-job actions. CV Checker presents literal education/experience evidence and skill tags. The five-column Board groups existing records and retains confirmed status updates and CSV export. Applications retain contact, eligibility, résumé and exact-message approval checks. Inbox shows recorded send attempts, with replies viewed in Gmail.

## Counters

| Card | Source |
|---|---|
| Active Loops | Saved loops with scheduled discovery enabled; the external scheduler is still required |
| Total Matches | Jobs meeting the account and loop thresholds after rescoring against the current résumé |
| Applications Submitted | Confirmed Gmail sends or manually confirmed submitted/response/interview/rejection records |
| Emails Sent | Stored Gmail message IDs only |
| Pending applications | Needs review, sending or delivery unknown records |

## Local use

Install Python 3.12, extract the complete source ZIP into a fresh folder and start `RUN_LOOPINGCV.bat`. After startup, open `http://localhost:8502` and keep the console open. No sign-in or PostgreSQL account is needed locally. Résumés and activity persist in the local development database. Email sending remains disabled locally.

Do not copy an old `.venv`: the user's earlier backup contained NumPy extensions for Python 3.14, which failed under Python 3.12. Keep previous data and backups private. See `LOCAL_RUN.md` for details.

## Verification

The existing PostgreSQL approval, tenancy, discovery and persistence checks remain in place. Additional checks cover current-resume dashboard counts, uncertain delivery states, checklist navigation and profile/answer persistence. Desktop and 390px browser checks exercise the actual forms, PDF upload, loop wizard, populated matches and Board, and locally disabled email approval controls using fictional fixtures. These checks do not establish real Gmail delivery, hosted deployment readiness or model accuracy. Windows launchers still require native Windows validation; this workspace runs Linux.
