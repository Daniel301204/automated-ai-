"""Private multi-user job review dashboard for Streamlit Community Cloud."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from live_sources import fetch_public
from resume_match import read_resume, score
from workflow import Store, evidence_profile, approval_digest

st.set_page_config(page_title='AutoJob AI', page_icon='🎯', layout='wide')
ROOT = Path(__file__).resolve().parent


def secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default


# Local test mode must be explicitly enabled; never enable it on a public deployment.
local = os.getenv('AUTOJOB_LOCAL_DEV') == '1'
if local:
    st.warning('Local development mode. Never enable AUTOJOB_LOCAL_DEV on a public host.')
    tenant = 'local-development'
    database_url = os.getenv('AUTOJOB_DATABASE_URL', 'sqlite:///data/development.db')
else:
    if not secret('auth') or not secret('database_url'):
        st.title('AutoJob AI setup')
        st.info('The owner must configure sign-in and PostgreSQL in Streamlit secrets before this app can accept résumés. See DEPLOYMENT.md.')
        st.stop()
    if not st.user.is_logged_in:
        st.title('Sign in to your private job workspace')
        if st.button('Sign in'):
            st.login()
        st.stop()
    if not st.user.get('sub'):
        st.error('Your identity provider did not return a stable user ID.')
        st.stop()
    tenant = hashlib.sha256((str(st.user.get('iss', 'configured-provider')) + ':' + st.user['sub']).encode()).hexdigest()
    database_url = secret('database_url')
    if not str(database_url).startswith('postgresql+psycopg://'):
        st.error('Hosted multi-user mode requires PostgreSQL with the psycopg driver.')
        st.stop()
    if st.sidebar.button('Sign out'):
        st.session_state.clear()
        st.logout()
        st.stop()


@st.cache_resource
def open_store(url):
    return Store(url)


try:
    Path('data').mkdir(exist_ok=True)
    store = open_store(database_url)
    user = store.profile(tenant)
    profile = json.loads(user['profile'])
except Exception:
    st.error('Private storage is unavailable. Check the database configuration; no résumé data has been loaded.')
    st.stop()

if st.session_state.get('tenant') != tenant:
    st.session_state.clear()
    st.session_state.tenant = tenant

gmail_connections = None
gmail = None
if not local and secret('gmail_oauth') and secret('token_encryption_key'):
    try:
        from gmail_connection import GmailConnections
        gmail_connections = GmailConnections(store.engine, secret('gmail_oauth'), secret('token_encryption_key'))
        if 'code' in st.query_params or 'state' in st.query_params:
            try:
                if not st.user.get('email') or not st.user.get('email_verified'):
                    raise ValueError('Sign in with a verified email before connecting Gmail.')
                gmail_connections.finish(tenant, st.user['email'], st.query_params.get('state'), st.query_params.get('code'))
                st.success('Your Gmail account is connected. Each send still requires approval.')
            except Exception:
                st.error('Gmail connection failed. Confirm you selected the same verified email as your sign-in, then start again.')
            finally:
                st.query_params.clear()
        gmail = gmail_connections.credentials(tenant)
    except Exception:
        st.error('Gmail connection configuration is unavailable. Email sending is disabled.')

page = st.sidebar.radio('Navigation', ['Find jobs', 'My résumé', 'Settings', 'Review & approve', 'Tracking'])
st.sidebar.caption('Each email requires your explicit approval. Scores are similarity estimates; eligibility requires evidence review.')
st.sidebar.caption('Scheduled discovery requires an external scheduler. Inbox synchronization is not enabled.')


def upload_resume(upload):
    if upload.size > 6 * 1024 * 1024:
        raise ValueError('Maximum résumé size is 6 MB')
    raw = upload.getvalue()
    text = read_resume(upload.name, raw)
    if len(text.strip()) < 45:
        raise ValueError('Not enough readable text. Use a text résumé or a selectable-text PDF; scanned PDFs require OCR.')
    store.save_profile(tenant, resume=raw, filename=upload.name, resume_text=text)
    st.session_state.pop('found_jobs', None)
    st.success('Résumé saved to your private workspace. Review the extracted text before applying.')


if page == 'My résumé':
    st.title('My résumé')
    upload = st.file_uploader('Upload PDF, DOCX or TXT', type=['pdf', 'docx', 'txt'])
    if upload and st.button('Save résumé'):
        try:
            upload_resume(upload)
            user = store.profile(tenant)
        except Exception as exc:
            st.error(str(exc))
    if user['resume_text']:
        st.caption('Evidence extraction uses literal résumé lines. It does not invent education, duration of experience or preferences.')
        st.json(evidence_profile(user['resume_text']))
        text = st.text_area('Review extracted text', user['resume_text'], height=300)
        if st.button('Save corrected text'):
            store.save_profile(tenant, resume_text=text)
            st.session_state.pop('found_jobs', None)
            st.success('Saved. Existing application drafts must be prepared again if the résumé changed.')
        st.download_button('Download original résumé', bytes(user['resume']), file_name=Path(user['filename']).name)
    else:
        st.info('Upload your résumé to begin.')

elif page == 'Settings':
    st.title('Job preferences')
    with st.form('preferences'):
        name = st.text_input('Your name (confirm from your résumé)', profile.get('name', ''))
        query = st.text_input('Role or keyword', profile.get('query', 'financial analyst'))
        locations = ['India + worldwide remote', 'India only', 'All locations']
        location = st.selectbox('Location preference', locations, index=locations.index(profile.get('location', locations[0])))
        threshold = st.number_input('Application match threshold (%)', 80, 100, int(profile.get('threshold', 80)))
        daily_limit = st.number_input('Daily application limit (UTC)', 1, 5, int(profile.get('daily_limit', 3)))
        enabled = st.checkbox('Activate scheduled discovery (owner must configure the scheduler)', value=profile.get('agent_enabled', False))
        gh = st.text_area('Greenhouse board tokens, one per line', '\n'.join(profile.get('boards', {}).get('greenhouse', [])))
        lv = st.text_area('Lever board tokens, one per line', '\n'.join(profile.get('boards', {}).get('lever', [])))
        if st.form_submit_button('Save preferences'):
            profile.update(name=name.strip(), query=query.strip(), location=location, threshold=threshold, daily_limit=daily_limit, agent_enabled=enabled,
                boards={'greenhouse': [s.strip() for s in gh.splitlines() if s.strip()], 'lever': [s.strip() for s in lv.splitlines() if s.strip()]})
            store.save_profile(tenant, profile=json.dumps(profile))
            st.success('Saved for your account.')
    st.caption('Email connection status: ' + ('connected' if gmail else 'not connected'))
    if gmail_connections and st.user.get('email') and st.user.get('email_verified'):
        if st.button('Connect my Gmail account'):
            st.link_button('Continue to Google consent', gmail_connections.authorize_url(tenant, st.user['email']))
        if gmail and st.button('Disconnect Gmail'):
            gmail_connections.disconnect(tenant)
            st.info('Connection removed from this app. You can also revoke access in your Google Account security settings.')
            st.rerun()
    else:
        st.info('The owner must configure Gmail OAuth before users can connect their own verified accounts.')
    st.info('ATS application integrations are not configured. Public Greenhouse and Lever feeds provide listings, not submission permission.')

elif page == 'Find jobs':
    st.title('Find and evaluate real jobs')
    if not user['resume_text']:
        st.info('Upload your résumé on My résumé first.')
    query = st.text_input('Role or keyword', profile.get('query', 'financial analyst'))
    if st.button('Find jobs', disabled=not bool(user['resume_text'])):
        if not query.strip():
            st.error('Enter a role or keyword.')
        else:
            try:
                with st.spinner('Checking public job feeds…'):
                    jobs, errors = fetch_public(query.strip(), profile.get('boards', {}), location_policy='all' if profile.get('location') == 'All locations' else 'india_remote')
                    if profile.get('location') == 'India only':
                        from live_sources import location_assessment
                        jobs = [j for j in jobs if location_assessment(j['location']) == 'India listed']
                    for job in jobs:
                        job.update(score(user['resume_text'], job))
                    jobs.sort(key=lambda j: j['match_score'], reverse=True)
                    store.remember(tenant, jobs)
                    st.session_state.found_jobs = jobs
                    st.session_state.feed_errors = errors
            except Exception:
                st.error('Discovery failed. Your saved jobs are preserved. Please retry later.')
    for error in st.session_state.get('feed_errors', []):
        st.warning(error)
    jobs = st.session_state.get('found_jobs', [])
    st.caption(f'{len(jobs)} listings retrieved. An empty result does not prove there are no vacancies.')
    for job in jobs[:100]:
        with st.expander(f"{job['title']} · {job['company']} · {job['match_score']}%"):
            st.write(job['location'])
            st.link_button('Original vacancy / employer application', job['url'])
            st.write(job['description'])
            st.write('Skills matched:', ', '.join(job['skills_matched']))
            st.write('Skills missing from résumé:', ', '.join(job['skills_missing']))
            st.caption(job['reason'])
            if st.button('Save job', key='save_' + job['job_id']):
                store.track(tenant, job['job_id'], 'saved')
                st.success('Saved')
    st.info('Review saved jobs on Review & approve. Verify mandatory requirements and the original employer contact before preparing an email.')

elif page == 'Review & approve':
    st.title('Review each application')
    st.warning('No ATS submission adapter is installed. Use the original employer page and record submission only after you have completed it.')
    review_rows = store.list_jobs(tenant)
    if not review_rows:
        st.info('Find and save jobs to review an application.')
        st.stop()
    review_labels = {r['job_id']: json.loads(r['payload'])['title'] + ' · ' + json.loads(r['payload'])['company'] for r in review_rows}
    selected_job = st.selectbox('Choose a vacancy to review', list(review_labels), format_func=review_labels.get)
    for row in [store.job(tenant, selected_job)]:
        job = json.loads(row['payload'])
        job.update(score(user['resume_text'] or '', job))
        with st.expander(f"{job['title']} · {job['company']} · {row['status']}"):
            st.link_button('Verify vacancy / apply on employer site', job['url'])
            st.write(job['description'])
            if row['status'] in ('sending', 'delivery_unknown') or row['reserved_day']:
                st.info('An email send has already been attempted for this vacancy. Check Tracking and your Gmail Sent folder; it will not be resent automatically.')
                continue
            if job['match_score'] < int(profile.get('threshold', 80)):
                st.info('Below your application threshold.')
                continue
            if not user['filename'] or not user['filename'].lower().endswith('.pdf'):
                st.info('For email, upload a reviewed PDF résumé. TXT/DOCX can be used for matching but are not silently converted or attached as a PDF.')
                continue
            if not profile.get('name'):
                st.info('Confirm your name in Settings first.')
                continue
            with st.form('prepare_' + job['job_id']):
                recipient = st.text_input('Verified application email', key='to_' + job['job_id'])
                evidence_url = st.text_input('Official page where this email is published', key='evidence_' + job['job_id'])
                contact = st.checkbox('I checked that this employer-published email accepts applications for this vacancy.')
                requirements = st.checkbox('I reviewed ALL mandatory criteria, location and work authorization; my résumé supports them.')
                verified = st.checkbox('I verified the résumé and candidate details against the original document.')
                subject = st.text_input('Subject', f"Application for {job['title']} — {profile['name']}")
                body = st.text_area('Message to review', f"Dear Hiring Team,\n\nI would like to apply for the {job['title']} role at {job['company']}. Please find my résumé attached for your review.\n\nVacancy: {job['url']}\n\nKind regards,\n{profile['name']}", height=180)
                if st.form_submit_button('Save application for final approval'):
                    import re
                    from guarded_upgrade import safe_employer_url
                    if not all((contact, requirements, verified)):
                        st.error('All verification checks must be confirmed; uncertain criteria need review.')
                    elif not safe_employer_url(evidence_url) or not re.fullmatch(r'[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+', recipient):
                        st.error('Supply an official HTTPS evidence page and one valid application email.')
                    elif not subject.strip() or '\n' in subject or '\r' in subject or not body.strip():
                        st.error('Supply a valid subject and message.')
                    else:
                        try:
                            app = dict(to=recipient, subject=subject, body=body, contact_evidence=evidence_url,
                                contact_verified=True, requirements_verified=True, profile_verified=True, score=job['match_score'],
                                resume_digest=hashlib.sha256(user['resume_text'].encode()).hexdigest())
                            store.prepare(tenant, job['job_id'], app, bytes(user['resume']))
                            st.success('Saved. Review the exact message and attachment below before approving.')
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
            if row['application']:
                app = json.loads(row['application'])
                st.write('**Recipient:**', app['to'])
                st.write('**Subject:**', app['subject'])
                st.text(app['body'])
                st.download_button('Review exact PDF attachment', bytes(row['attachment']), file_name='Resume.pdf', key='pdf_' + job['job_id'])
                digest = approval_digest(app['to'], app['subject'], app['body'], bytes(row['attachment']))
                approved = st.checkbox('I approve sending this exact email and PDF to this recipient now.', key='approval_' + digest)
                if not gmail:
                    st.info('Your Gmail OAuth connection is not configured. Sending remains disabled.')
                if st.button('Approve and send this email', key='send_' + digest, disabled=not (approved and gmail)):
                    try:
                        store.send_approved(tenant, job['job_id'], digest, gmail, int(profile.get('daily_limit', 3)))
                        st.success('Gmail accepted the message. Tracking now shows awaiting response; this does not prove inbox delivery.')
                    except (ValueError, RuntimeError) as exc:
                        st.error(str(exc))
                    except Exception:
                        st.error('Storage or email operation failed. Check Tracking and Gmail Sent before retrying.')

else:
    st.title('Track applications')
    rows = store.list_jobs(tenant)
    if not rows:
        st.info('Find jobs to start your tracker.')
    else:
        records = [dict(title=json.loads(r['payload'])['title'], company=json.loads(r['payload'])['company'], status=r['status'], gmail_message_id=r['message_id'] or '') for r in rows]
        st.dataframe(pd.DataFrame(records), hide_index=True)
        st.download_button('Export tracking CSV', pd.DataFrame(records).to_csv(index=False).encode(), 'applications.csv')
        st.caption('Gmail acceptance is recorded automatically. Interviews, rejections and external ATS submissions must be confirmed manually; inbox synchronization is not implemented.')
        choices = {r['job_id']: json.loads(r['payload'])['title'] + ' · ' + json.loads(r['payload'])['company'] for r in rows}
        job_id = st.selectbox('Application', list(choices), format_func=choices.get)
        status = st.selectbox('Confirmed status', ['needs_review', 'submitted', 'awaiting_response', 'interview', 'rejected'])
        confirmed = st.checkbox('I confirm this status reflects an actual employer response or completed submission.')
        if st.button('Record status', disabled=not confirmed):
            try:
                store.track(tenant, job_id, status)
                st.success('Updated')
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
