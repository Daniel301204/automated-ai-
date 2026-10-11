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
from loops import SOURCES, LOCATIONS, SUBJECT, BODY, normalize_loop, validate_template, email_preview, discover_loop
from looping_ui import (theme, sidebar, header, stepper, empty, go, public_share_url,
    description, status_badge, job_heading, skill_chips, dashboard_counts, overview_cards, setup_item, greeting)

st.set_page_config(page_title='LoopingCV', page_icon='↻', layout='wide')
theme()
ROOT = Path(__file__).resolve().parent


def secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default


# Local test mode must be explicitly enabled; never enable it on a public deployment.
local = os.getenv('AUTOJOB_LOCAL_DEV') == '1'
if local:
    tenant = 'local-development'
    database_url = os.getenv('AUTOJOB_DATABASE_URL', 'sqlite:///data/development.db')
else:
    if not secret('auth') or not secret('database_url'):
        from public_demo import render_public_demo
        render_public_demo(ROOT)
        with st.expander('Owner setup: enable private workspaces'):
            st.write('Google sign-in settings: ' + ('present' if secret('auth') else 'missing [auth] section'))
            st.write('PostgreSQL storage: ' + ('present' if secret('database_url') else 'missing database_url'))
            st.write('1. Open your Streamlit app settings → Secrets.')
            st.write('2. Create a managed PostgreSQL database and a Google OAuth Web application client.')
            st.write('3. Copy the secrets template, replace its placeholders privately, save and restart the app.')
            st.caption('Google callbacks use your actual public app URL: /oauth2callback for sign-in and / for Gmail. Each friend has a separate account. Gmail sending needs additional OAuth/encryption settings and approval for every message.')
            public_origin = public_share_url(st.context.url)
            if public_origin:
                st.write('**Google callback addresses for this app**')
                st.code('Sign-in: ' + public_origin + 'oauth2callback\nGmail: ' + public_origin, language=None)
                template = (ROOT / '.streamlit' / 'secrets.example.toml').read_text().replace('https://YOUR_APP.streamlit.app', public_origin.rstrip('/'))
                st.download_button('Download secrets template for this app', template, 'loopingcv-secrets-template.toml', 'text/plain')
            guide = 'https://github.com/Daniel301204/automated-ai-/blob/codex/approval-gated-streamlit/'
            st.link_button('Open simple hosting checklist', guide + 'CAPSTONE_LAUNCH.md')
            st.link_button('Open secrets template', guide + '.streamlit/secrets.example.toml')
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

st.session_state.setdefault('active_page', 'Overview')
auth_settings = secret('auth', {}) if not local else {}
sidebar(public_share_url(auth_settings.get('redirect_uri')))
page = st.session_state.active_page
header(page, local, profile.get('name', ''))
if not local and st.sidebar.button('Sign out'):
    st.session_state.clear()
    st.logout()
    st.stop()


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


def run_search(config, loop_id=None):
    try:
        with st.spinner('Checking public job feeds…'):
            jobs, errors = discover_loop(config, user['resume_text'] or '')
            for job in jobs:
                job.update(loop_id=loop_id, loop_threshold=config.get('threshold',80), loop_limit=config.get('daily_limit',3), email_subject=config.get('subject',SUBJECT), email_body=config.get('body',BODY))
            store.remember(tenant, jobs)
            st.session_state.found_jobs = jobs
            st.session_state.feed_errors = errors
            go('All Matches')
        st.rerun()
    except Exception:
        st.error('Discovery failed. Your saved jobs are preserved. Please retry later.')


if page == 'New Loop':
    with st.container(key='loop_content'):
        st.markdown('<div class="lc-intro"><h1>Let’s create a new Loop ⓘ</h1><p>Automate your job search</p></div>', unsafe_allow_html=True)
        step = st.session_state.setdefault('wizard_step', 0)
        draft = st.session_state.setdefault('loop_draft', dict(query='', location=LOCATIONS[0], sources=SOURCES.copy(), threshold=80, daily_limit=3, subject=SUBJECT, body=BODY, boards=profile.get('boards', {}), remote_only=False))
        stepper(step)
        with st.container(key='wizard_card'):
            if step == 0:
                st.subheader('Complete your desired job info and location')
                with st.form('search_info'):
                    query = st.text_input('Job Titles', draft['query'], placeholder='Software Engineer')
                    st.caption('This job title or keyword will be used to search public job feeds.')
                    location = st.selectbox('Job Location', LOCATIONS, index=LOCATIONS.index(draft['location']))
                    radius_label, radius_control = st.columns([1,5], vertical_alignment='center')
                    radius_label.write('Distance radius')
                    with radius_control:
                        st.slider('Distance radius', 0, 150, 30, disabled=True, label_visibility='collapsed')
                        st.caption('Distance filtering is unavailable for the current job feeds.')
                    remote = st.checkbox('Search only for remote jobs', draft.get('remote_only', False))
                    st.checkbox('Search only for hybrid jobs', disabled=True, help='Hybrid eligibility is not consistently available from these feeds.')
                    sources = st.multiselect('Search in Specific Job Boards', SOURCES, default=draft['sources'])
                    st.caption('Choose the providers for this loop. Employer feeds need board tokens in Settings.')
                    if st.form_submit_button('Continue', type='primary'):
                        if not query.strip() or not sources:
                            st.error('Enter a job title and select at least one source.')
                        else:
                            draft.update(query=query.strip(), location=location, remote_only=remote, sources=sources)
                            st.session_state.wizard_step = 1
                            st.rerun()
                with st.expander('Your CV', expanded=not bool(user['resume_text'])):
                    if user['resume_text']:
                        st.success('A résumé is saved in your private workspace.')
                    upload = st.file_uploader('Upload PDF, DOCX or TXT', type=['pdf', 'docx', 'txt'])
                    if upload and st.button('Save résumé'):
                        try:
                            upload_resume(upload)
                        except Exception as exc:
                            st.error(str(exc))
            elif step == 1:
                st.subheader('Write your application email template')
                st.caption('Use {job_title}, {company}, {name} and {job_url}. You will review the filled message before each send.')
                with st.form('email_template'):
                    subject = st.text_input('Email Subject', draft['subject'])
                    body = st.text_area('Email Message', draft['body'], height=250)
                    if st.form_submit_button('Continue', type='primary'):
                        try:
                            validate_template(subject); validate_template(body)
                            if '\n' in subject or '\r' in subject:
                                raise ValueError('Email subjects cannot contain line breaks')
                            draft.update(subject=subject, body=body)
                            st.session_state.wizard_step = 2
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
            elif step == 2:
                st.subheader('Choose your loop settings')
                with st.form('loop_settings'):
                    name = st.text_input('Loop Name', draft.get('name', draft['query']))
                    threshold = st.number_input('Minimum application match (%)', 80, 100, int(draft['threshold']))
                    limit = st.number_input('Maximum daily emails while using this loop (UTC)', 1, 5, int(draft['daily_limit']))
                    st.checkbox('Require my approval before every email', value=True, disabled=True)
                    gh = st.text_area('Greenhouse employer board tokens, one per line', '\n'.join(draft.get('boards', {}).get('greenhouse', [])))
                    lv = st.text_area('Lever employer board tokens, one per line', '\n'.join(draft.get('boards', {}).get('lever', [])))
                    if st.form_submit_button('Continue', type='primary'):
                        try:
                            draft.update(name=name, threshold=threshold, daily_limit=limit, boards={'greenhouse':[s.strip() for s in gh.splitlines() if s.strip()], 'lever':[s.strip() for s in lv.splitlines() if s.strip()]})
                            normalize_loop(draft)
                            st.session_state.wizard_step = 3
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
            else:
                st.subheader('Review your new loop')
                st.write('**Job title:**', draft['query'])
                st.write('**Location:**', draft['location'])
                st.write('**Sources:**', ', '.join(draft['sources']))
                st.write('**Minimum match:**', str(draft['threshold']) + '%')
                st.write('**Daily email cap:**', str(draft['daily_limit']) + ' · Account-wide cap also applies')
                st.text(draft['subject'] + '\n\n' + draft['body'])
                st.info('Every application needs eligibility and contact verification plus your approval. Creating a loop does not send applications.')
                enabled = st.checkbox('Activate scheduled discovery for this loop', help='Requires the external scheduler described in the deployment guide.')
                if not user['resume_text']:
                    st.caption('Upload your CV on CV Checker before running this loop.')
                if st.button('Create Loop', type='primary'):
                    try:
                        store.save_loop(tenant, draft, enabled)
                        st.session_state.pop('loop_draft', None)
                        st.session_state.wizard_step = 0
                        go('My loops')
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
            if step > 0 and st.button('Back'):
                st.session_state.wizard_step = step - 1
                st.rerun()

elif page == 'Overview':
    rows = store.list_jobs(tenant)
    saved_loops = store.list_loops(tenant)
    st.subheader('You’re almost there!' if not (profile.get('name') and user['resume_text'] and saved_loops) else 'Your workspace is ready')
    with st.container(key='setup_panel'):
        setup_item('Setup profile', 'person', bool(profile.get('name')), 'Personal Info', 'profile')
        setup_item('Answer questions', 'questions', bool(profile.get('answers')), 'Questions', 'answers')
        setup_item('Start first loop', 'loop', bool(saved_loops), 'New Loop', 'loop')
        setup_item('Upload your CV', 'document', bool(user['resume_text']), 'CV Checker', 'cv')
    greeting(profile.get('first_name') or profile.get('name', '').split(' ', 1)[0])
    overview_cards(dashboard_counts(rows, saved_loops, user['resume_text'], profile.get('threshold', 80)))
    st.caption('Counts reflect your saved activity. Scheduled discovery needs the external scheduler; every email requires your approval.')
    if rows:
        with st.expander('Recent saved jobs'):
            for row in rows[-5:][::-1]:
                job_heading(json.loads(row['payload']))
                status_badge(row['status'])
            st.button('Review applications', on_click=go, args=('My Applications',))

elif page == 'My loops':
    st.title('My loops')
    description('Organize your searches by role, location and application preferences.')
    saved_loops = store.list_loops(tenant)
    if not saved_loops:
        empty('Create your first loop', 'Save a job title, location and email template to organize your search.')
        st.button('Create a new loop', type='primary', on_click=go, args=('New Loop',))
    for row in saved_loops:
        config = json.loads(row['config'])
        with st.container(border=True):
            title_col, status_col = st.columns([4,1])
            title_col.subheader(config['name'])
            with status_col:
                status_badge('active' if row['enabled'] else 'paused')
            st.caption(config['query'] + ' · ' + config['location'] + ' · ' + ', '.join(config['sources']))
            st.caption('Match threshold: ' + str(config['threshold']) + '% · Daily email limit: ' + str(config['daily_limit']) + ' · Your approval required')
            if row['enabled']:
                st.caption('Scheduled discovery is enabled for the external scheduler.')
            run_col, pause_col, edit_col = st.columns(3)
            if run_col.button('Find matches now', key='run_loop_' + row['loop_id'], type='primary', disabled=not bool(user['resume_text'])):
                run_search(config, row['loop_id'])
            if pause_col.button('Pause loop' if row['enabled'] else 'Activate loop', key='toggle_' + row['loop_id']):
                store.set_loop_enabled(tenant, row['loop_id'], not row['enabled'])
                st.rerun()
            if edit_col.button('Use as a new loop', key='copy_' + row['loop_id']):
                st.session_state.loop_draft = config
                st.session_state.wizard_step = 0
                go('New Loop')
                st.rerun()
    if not user['resume_text']:
        st.info('Upload your résumé on CV Checker to run a search.')

elif page == 'Personal Info':
    with st.container(key='personal_card'):
        st.subheader('This info will be used in your job applications.')
        personal, account, questions, pricing, notifications = st.tabs(['Personal info', 'Account Settings', 'Questions', 'Pricing Plan', 'Notifications'])
        with personal:
            with st.container(key='personal_form'):
                with st.form('personal_info'):
                    st.text_input('Email', st.user.get('email','') if not local else '', disabled=True, placeholder='No sign-in required in local mode' if local else 'Your verified sign-in email')
                    pieces = profile.get('name', '').split(' ', 1)
                    first = st.text_input('First Name', profile.get('first_name', pieces[0] if pieces else ''))
                    last = st.text_input('Last Name', profile.get('last_name', pieces[1] if len(pieces)>1 else ''))
                    st.toggle('Enable AI answering on applications', value=False, disabled=True)
                    st.caption('Automatic answering is not implemented. Review answers using your own evidence.')
                    location = st.text_input('Location', profile.get('home_location', ''), placeholder='e.g. Chennai, India')
                    phone = st.text_input('Phone (optional)', profile.get('phone', ''))
                    if st.form_submit_button('Save personal info', type='primary'):
                        if not first.strip():
                            st.error('Enter your first name as it appears on your résumé.')
                        else:
                            profile.update(first_name=first.strip(), last_name=last.strip(), name=(first.strip()+' '+last.strip()).strip(), home_location=location.strip(), phone=phone.strip())
                            store.save_profile(tenant, profile=json.dumps(profile))
                            st.success('Personal info saved privately to your account.')
        with account:
            with st.form('preferences'):
                st.subheader('Application preferences')
                threshold = st.number_input('Account application match threshold (%)', 80, 100, int(profile.get('threshold',80)))
                limit = st.number_input('Account daily email cap (UTC)', 1, 5, int(profile.get('daily_limit',3)))
                if st.form_submit_button('Save preferences'):
                    profile.update(threshold=threshold, daily_limit=limit)
                    store.save_profile(tenant, profile=json.dumps(profile))
                    st.success('Saved')
            st.caption('Gmail: ' + ('connected' if gmail else 'not connected'))
            if gmail_connections and st.user.get('email') and st.user.get('email_verified'):
                if st.button('Connect my Gmail account'):
                    st.link_button('Continue to Google consent', gmail_connections.authorize_url(tenant, st.user['email']))
                if gmail and st.button('Disconnect Gmail'):
                    gmail_connections.disconnect(tenant)
                    st.rerun()
            else:
                st.info('Email sending is disabled in local preview. Gmail can be connected in the authenticated hosted version.' if local else 'Gmail connection is not configured. The owner must add Google OAuth settings before users can connect.')
        with questions:
            st.write('Save only truthful answers you have checked. These are reference notes, not automatically submitted answers.')
            answers = st.text_area('My verified application answers', profile.get('answers',''), height=180)
            if st.button('Save answers'):
                profile['answers'] = answers
                store.save_profile(tenant, profile=json.dumps(profile))
                st.success('Saved privately')
        with pricing:
            st.info('No paid plans or billing are configured for LoopingCV.')
        with notifications:
            st.info('View confirmed application activity in My Applications and Inbox. Automated inbox synchronization is not enabled.')

elif page == 'Questions':
    st.title('Questions')
    description('Keep your verified application answers ready, and find help with your job search.')
    with st.container(key='content_card'):
        st.subheader('Your application answers')
        st.caption('Reference notes only. Save truthful answers supported by your documents; they are not automatically submitted.')
        answers = st.text_area('My verified application answers', profile.get('answers',''), height=180, key='questions_answers')
        if st.button('Save answers', type='primary', key='questions_save'):
            profile['answers'] = answers
            store.save_profile(tenant, profile=json.dumps(profile))
            st.success('Saved privately')
    st.subheader('Frequently asked questions')
    for question, answer in [('Will a loop send applications automatically?', 'No. Scheduled discovery only finds jobs. You verify eligibility and contact information, then explicitly approve each email.'), ('Does a match score prove I am eligible?', 'No. The score compares résumé keywords. Review all mandatory qualifications, location and work authorization.'), ('Can LoopingCV submit ATS forms?', 'No authorized ATS adapters are configured. Complete the employer application yourself and record its status.'), ('Why are radius and hybrid filters disabled?', 'The public feeds do not provide consistent distance coordinates or hybrid eligibility.'), ('Are my details shared with other users?', 'Your profile, CV, loops, jobs and Gmail connection belong to your signed-in account.'), ('Why is an email marked delivery_unknown?', 'Gmail did not confirm the result. Check your Gmail Sent folder; the app blocks retries to avoid duplicate applications.')]:
        with st.expander(question):
            st.write(answer)
    st.button('Personal info & verified answers', on_click=go, args=('Personal Info',))

elif page == 'CV Builder':
    st.title('CV Builder')
    description('Review and refine your résumé using your own verified experience.')
    with st.container(key='content_card'):
        st.subheader('Build from your verified evidence')
        st.caption('This editor does not invent qualifications or experience. It exports plain text; email applications require your reviewed original PDF.')
        if not user['resume_text']:
            empty('Start with your own CV', 'Upload a résumé on CV Checker before using the editor.')
            st.button('Upload my CV', on_click=go, args=('CV Checker',))
        else:
            text = st.text_area('Your résumé text', user['resume_text'], height=400)
            verified = st.checkbox('I checked these details against my original documents.')
            if st.button('Save verified text', disabled=not verified):
                store.save_profile(tenant, resume_text=text)
                st.session_state.pop('found_jobs', None)
                st.success('Saved. Existing email drafts require a new review if evidence changed.')
            st.download_button('Download text CV', text.encode('utf-8'), 'LoopingCV-resume.txt', mime='text/plain')

elif page == 'Inbox':
    st.title('Inbox')
    description('Your recorded email application activity, in one place.')
    st.info('View employer replies in Gmail. Automatic reply synchronization is unavailable; this page shows recorded send attempts.')
    sent = [r for r in store.list_jobs(tenant) if r['reserved_day']]
    if not sent:
        empty('No dispatched applications yet', 'Emails appear here after you approve a send attempt.')
    for row in sent:
        job = json.loads(row['payload'])
        with st.container(border=True):
            job_heading(job)
            status_badge(row['status'])
            st.caption('Attempt date (UTC): ' + row['reserved_day'])
            if row['message_id']:
                st.write('Gmail message ID:', row['message_id'])
    st.link_button('Open Gmail', 'https://mail.google.com/')

elif page == 'CV Checker':
    st.title('CV Checker')
    description('Upload once, check what was extracted and keep your résumé ready for applications.')
    with st.container(key='cv_upload'):
        st.subheader('Your résumé')
        st.caption('PDF, DOCX or TXT · Up to 6 MB · Scanned PDFs require OCR, which is unavailable.')
        upload = st.file_uploader('Upload PDF, DOCX or TXT', type=['pdf', 'docx', 'txt'])
        if upload and st.button('Save résumé', type='primary'):
            try:
                upload_resume(upload)
                user = store.profile(tenant)
            except Exception as exc:
                st.error(str(exc))
    if user['resume_text']:
        evidence = evidence_profile(user['resume_text'])
        st.subheader('Skills found in your résumé')
        if evidence['skills']:
            skill_chips(evidence['skills'])
        else:
            st.caption('No predefined skills found. You can still use résumé keywords for matching.')
        education, experience = st.columns(2)
        with education, st.container(border=True):
            st.subheader('Education evidence')
            for line in evidence['education_evidence']:
                st.write(line)
            if not evidence['education_evidence']:
                st.caption('No education lines identified. Check your original résumé.')
        with experience, st.container(border=True):
            st.subheader('Experience evidence')
            for line in evidence['experience_evidence']:
                st.write(line)
            if not evidence['experience_evidence']:
                st.caption('No experience lines identified. Check your original résumé.')
        st.caption('These are literal résumé lines. Confirm accuracy against your original document.')
        text = st.text_area('Review extracted text', user['resume_text'], height=300)
        if st.button('Save corrected text'):
            store.save_profile(tenant, resume_text=text)
            st.session_state.pop('found_jobs', None)
            st.success('Saved. Existing application drafts must be prepared again if the résumé changed.')
        st.download_button('Download original résumé', bytes(user['resume']), file_name=Path(user['filename']).name)
    else:
        st.info('Upload your résumé to begin.')

elif page in ('Search Jobs', 'All Matches'):
    st.title(page)
    description('Discover real vacancies and review how their requirements compare with your résumé.' if page == 'Search Jobs' else 'Review vacancies that meet your loop and account match thresholds.')
    if not user['resume_text']:
        st.info('Upload your résumé on CV Checker first.')
    saved_loops = store.list_loops(tenant)
    loop_options = {'quick': 'Quick search'}
    loop_options.update({r['loop_id']: json.loads(r['config'])['name'] for r in saved_loops})
    with st.container(key='search_controls'):
        source_col, query_col, action_col = st.columns([2,3,1])
        with source_col:
            selected = st.selectbox('Search loop', list(loop_options), format_func=loop_options.get)
        selected_config = next((json.loads(r['config']) for r in saved_loops if r['loop_id']==selected), None)
        with query_col:
            query = st.text_input('Job title or keyword', selected_config['query'] if selected_config else profile.get('query', ''), placeholder='Software Engineer', key='query_' + selected)
        with action_col:
            if st.button('Find jobs', disabled=not bool(user['resume_text']), type='primary', use_container_width=True):
                config = dict(selected_config or dict(location=LOCATIONS[0], sources=SOURCES, threshold=80, daily_limit=3, boards=profile.get('boards',{}), subject=SUBJECT, body=BODY))
                config['query'] = query
                run_search(config, None if selected=='quick' else selected)
    for error in st.session_state.get('feed_errors', []):
        st.warning(error)
    jobs = st.session_state.get('found_jobs')
    if jobs is None:
        jobs = [json.loads(r['payload']) for r in store.list_jobs(tenant)]
    for job in jobs:
        job.update(score(user['resume_text'] or '', job))
    if page == 'All Matches':
        jobs = [j for j in jobs if j.get('match_score',0) >= max(int(j.get('loop_threshold',80)), int(profile.get('threshold',80)))]
    st.caption(f'{len(jobs)} listings retrieved. An empty result does not prove there are no vacancies.')
    if not jobs:
        empty('Your matches will appear here', 'Choose a job title and run a search after uploading your résumé.')
    for job in jobs[:100]:
        with st.container(border=True):
            details, rating = st.columns([4,1])
            with details:
                job_heading(job)
                skill_chips(job['skills_matched'])
            with rating:
                st.metric('Match', str(job['match_score']) + '%')
            with st.expander('View requirements and match details'):
                st.write(job['description'])
                st.write('Skills missing from résumé:', ', '.join(job['skills_missing']))
                st.caption(job['reason'])
            employer, save = st.columns([4,1])
            employer.link_button('Original vacancy / employer application', job['url'])
            if save.button('Save job', key='save_' + job['job_id']):
                store.track(tenant, job['job_id'], 'saved')
                st.success('Saved')
    st.info('Review saved jobs on My Applications. Verify mandatory requirements and the original employer contact before preparing an email.')

elif page == 'My Applications':
    st.title('My Applications')
    description('Verify the vacancy, review your message and approve each application yourself.')
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
            job_heading(job)
            status_badge(row['status'])
            st.link_button('Verify vacancy / apply on employer site', job['url'])
            st.write(job['description'])
            if row['status'] in ('sending', 'delivery_unknown') or row['reserved_day']:
                st.info('An email send has already been attempted for this vacancy. Check Tracking and your Gmail Sent folder; it will not be resent automatically.')
                continue
            if job['match_score'] < max(int(profile.get('threshold', 80)), int(job.get('loop_threshold',80))):
                st.info('Below your application threshold.')
                continue
            if not user['filename'] or not user['filename'].lower().endswith('.pdf'):
                st.info('For email, upload a reviewed PDF résumé. TXT/DOCX can be used for matching but are not silently converted or attached as a PDF.')
                continue
            if not profile.get('name'):
                st.info('Confirm your name in Personal Info first.')
                continue
            with st.form('prepare_' + job['job_id']):
                recipient = st.text_input('Verified application email', key='to_' + job['job_id'])
                evidence_url = st.text_input('Official page where this email is published', key='evidence_' + job['job_id'])
                contact = st.checkbox('I checked that this employer-published email accepts applications for this vacancy.')
                requirements = st.checkbox('I reviewed ALL mandatory criteria, location and work authorization; my résumé supports them.')
                verified = st.checkbox('I verified the résumé and candidate details against the original document.')
                default_subject, default_body = email_preview({'subject': job.get('email_subject',SUBJECT), 'body':job.get('email_body',BODY)}, job, profile['name'])
                subject = st.text_input('Subject', default_subject)
                body = st.text_area('Message to review', default_body, height=180)
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
                                contact_verified=True, requirements_verified=True, profile_verified=True, score=job['match_score'], loop_threshold=job.get('loop_threshold',80), loop_limit=job.get('loop_limit',5),
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
                    if local:
                        st.info('Email sending is disabled in local preview. Publish the authenticated app with PostgreSQL, then connect your Gmail in Personal Info → Account Settings. Every email requires your approval.')
                    else:
                        st.info('Connect your Gmail in Personal Info → Account Settings before sending. The owner must configure Google OAuth if the connection option is unavailable.')
                if st.button('Approve and send this email', key='send_' + digest, disabled=not (approved and gmail)):
                    try:
                        store.send_approved(tenant, job['job_id'], digest, gmail, int(profile.get('daily_limit', 3)))
                        st.success('Gmail accepted the message. Tracking now shows awaiting response; this does not prove inbox delivery.')
                    except (ValueError, RuntimeError) as exc:
                        st.error(str(exc))
                    except Exception:
                        st.error('Storage or email operation failed. Check Tracking and Gmail Sent before retrying.')

else:
    st.title('Board')
    description('Follow your applications from review to employer response.')
    rows = store.list_jobs(tenant)
    if not rows:
        st.info('Find jobs to start your tracker.')
    else:
        records = [dict(title=json.loads(r['payload'])['title'], company=json.loads(r['payload'])['company'], status=r['status'], gmail_message_id=r['message_id'] or '') for r in rows]
        stages = [('Needs review', ('discovered','saved','needs_review','sending','delivery_unknown')), ('Submitted', ('submitted',)), ('Awaiting response', ('awaiting_response',)), ('Interview', ('interview',)), ('Rejected', ('rejected',))]
        with st.container(key='board_columns'):
            for column, (label, statuses) in zip(st.columns(5), stages):
                with column:
                    group = [row for row in rows if row['status'] in statuses]
                    import html
                    st.markdown('<div class="lc-board-label">' + html.escape(label) + '<span class="lc-board-count">' + str(len(group)) + '</span></div>', unsafe_allow_html=True)
                    if not group:
                        st.caption('No applications')
                    for row in group:
                        with st.container(border=True):
                            job_heading(json.loads(row['payload']))
                            status_badge(row['status'])
        with st.expander('All application records'):
            st.dataframe(pd.DataFrame(records), hide_index=True, use_container_width=True)
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
