"""Public, read-only capstone demonstration; no uploads, storage or email transport."""
from pathlib import Path

import streamlit as st

from looping_ui import stepper
from resume_match import score
from workflow import evidence_profile


SAMPLE_JOBS = {
    'Python Developer': 'Python developer using SQL, Streamlit, Git and Docker.',
    'Frontend Developer': 'Frontend developer using JavaScript, React and TypeScript.',
}


def render_public_demo(root: Path) -> None:
    # Only this shipped fictional fixture is read. User files, stores and credentials
    # are never loaded, and there is no send handler in this public route.
    resume = (root / 'docs' / 'capstone' / 'demo_resume.txt').read_text(encoding='utf-8')
    evidence = evidence_profile(resume)
    st.title('↻ LoopingCV')
    st.info('Public demo · Fictional résumé and job examples. Uploads and email sending are disabled. '
            'Private workspaces become available after the owner configures sign-in and PostgreSQL.')
    overview, loop, cv, matches, applications = st.tabs([
        'Overview', 'New Loop', 'CV Checker', 'All Matches', 'My Applications',
    ])
    with overview:
        st.subheader('Explore the job application workflow')
        st.write('Résumé evidence → search preferences → matching → review → explicit email approval.')
        left, middle, right = st.columns(3)
        left.metric('Sample résumé', '1')
        middle.metric('Fictional job examples', str(len(SAMPLE_JOBS)))
        right.metric('Applications sent', '0')
        st.write('Use the tabs to inspect the sample résumé, a loop configuration and the actual keyword matcher.')
        st.caption('These examples are not real vacancies. Scores measure text similarity, not eligibility or model accuracy.')
    with loop:
        st.subheader('Let’s create a new Loop')
        st.caption('Example configuration · Read only; no search or saved loop is created here.')
        stepper(0)
        st.text_input('Job Titles', 'Python Developer', disabled=True)
        st.selectbox('Job Location', ['India / worldwide remote'], disabled=True)
        st.checkbox('Search only for remote jobs', value=True, disabled=True)
        st.slider('Example match threshold', 80, 100, 80, disabled=True)
        st.number_input('Example daily email limit', min_value=1, max_value=5, value=3, disabled=True)
        st.checkbox('Require my approval before every email', value=True, disabled=True)
        st.button('Save loop — requires a private workspace', disabled=True)
    with cv:
        st.subheader('Fictional résumé evidence')
        st.code(resume, language=None)
        st.write('**Skills extracted:** ' + ', '.join(evidence['skills']))
        st.write('**Education evidence:**')
        for line in evidence['education_evidence']:
            st.write(line)
        st.write('**Experience evidence:**')
        for line in evidence['experience_evidence']:
            st.write(line)
        st.caption('The extractor reads literal evidence. Preferences require user confirmation. '
                   'Public résumé uploads are unavailable until the private workspace is configured.')
    with matches:
        st.subheader('Try the matcher on fictional examples')
        title = st.selectbox('Fictional role', list(SAMPLE_JOBS), key='public_demo_role')
        job = dict(title=title, description=SAMPLE_JOBS[title])
        result = score(resume, job)
        st.write(job['description'])
        st.metric('Text similarity', str(result['match_score']) + '%')
        st.write('**Matched skills:** ' + (', '.join(result['skills_matched']) or 'None'))
        st.write('**Missing skills:** ' + (', '.join(result['skills_missing']) or 'None identified'))
        st.warning(result['reason'])
    with applications:
        st.subheader('Application review example')
        st.caption('Illustration only. This draft has no recipient and cannot be sent.')
        st.text_input('Application contact', '', placeholder='Verify on the employer’s official page', disabled=True)
        st.text_input('Subject', 'Application for Python Developer', disabled=True)
        st.text_area('Sample email',
                     'Hello hiring team,\n\nI would like to apply for the Python Developer role. '
                     'My sample résumé includes Python, SQL, Streamlit and Git.\n\nThank you.', disabled=True)
        st.checkbox('I verified the vacancy, eligibility, contact and résumé', disabled=True)
        st.checkbox('I approve sending this exact email and PDF', disabled=True)
        st.button('Approve and send — unavailable in public demo', disabled=True)
        st.write('**Demo status:** Needs review · No application submitted.')
        st.caption('Automatic ATS submission and employer reply synchronization are further development tasks.')
