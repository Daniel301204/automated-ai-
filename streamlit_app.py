"""AutoJob AI: résumé-first live job search and match dashboard."""
from __future__ import annotations
import csv,io,json,os
from pathlib import Path
from urllib.parse import quote_plus
import pandas as pd
import streamlit as st
from live_sources import fetch_public, portals
from resume_match import read_resume, score,skills_in
from job_store import connect,upsert,set_status
from guarded_upgrade import gate, create_tailored_pdf, verified_email, draft_email, init_actions, queue_application, safe_employer_url

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data';DATA.mkdir(exist_ok=True)
st.set_page_config(page_title='AutoJob AI | Find your next role',page_icon='🎯',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
.block-container {padding-top:1.8rem;max-width:1300px}div[data-testid="stMetric"]{border:1px solid #e3e8ed;padding:12px 18px;border-radius:14px;background:#fafcff}
.jobmeta{color:#64748b;font-size:0.92rem}.intro{color:#64748b;font-size:1.05rem;margin-top:-8px}.brand{font-size:2.0rem;font-weight:750;letter-spacing:-1px}
</style>''',unsafe_allow_html=True)

def safe_json(file,default):
    try:return json.loads((ROOT/file).read_text(encoding='utf-8'))
    except (FileNotFoundError,json.JSONDecodeError):return default

def save_resume(upload):
    if upload.size > 6*1024*1024: raise ValueError('Maximum résumé size is 6 MB')
    raw=upload.getvalue(); plain=read_resume(upload.name,raw)
    if len(plain.strip())<45: raise ValueError('Could not extract enough text; try a selectable-text résumé or TXT')
    suffix=upload.name.lower().rsplit('.',1)[-1]
    (DATA/('resume.'+suffix)).write_bytes(raw)
    (DATA/'resume_text.txt').write_text(plain,encoding='utf-8')
    return plain

if 'resume' not in st.session_state:
    previous=DATA/'resume_text.txt'
    st.session_state.resume=previous.read_text(encoding='utf-8') if previous.exists() else ''
if 'jobs' not in st.session_state:st.session_state.jobs=[]
if 'errors' not in st.session_state:st.session_state.errors=[]

with st.sidebar:
    st.markdown('## 🎯 AutoJob AI')
    st.caption('Your résumé. Your matching jobs. One dashboard.')
    page=st.radio('Navigation',['🔍 Find matching jobs','📄 My résumé','🛡️ Guarded applications','⭐ Saved & tracked jobs','⚙️ Sources & settings'],label_visibility='collapsed')
    st.divider()
    st.info('**Live search:** Himalayas, Remotive and configured employer feeds. LinkedIn, Indeed and Naukri are opened through direct search links, not scraped.')
    st.caption('Application preparation is review-only until eligibility and recipient are verified. No emails or ATS submissions are triggered by this dashboard.')

if page=='📄 My résumé':
    st.title('📄 My résumé')
    st.write('Upload your résumé once. Your extracted text is stored locally for future searches.')
    upload=st.file_uploader('Upload PDF, DOCX or TXT',type=['pdf','docx','txt'])
    if upload and st.button('Extract résumé',type='primary'):
        try:
            st.session_state.resume=save_resume(upload);st.success('Résumé extracted and saved locally.')
        except Exception as e:st.error(str(e))
    if st.session_state.resume:
        st.metric('Words extracted',len(st.session_state.resume.split()))
        sk=sorted(skills_in(st.session_state.resume));st.write('**Recognized skills:**',', '.join(sk) if sk else 'No predefined skills recognized; keyword matching still works.')
        with st.expander('Review extracted résumé text'):
            updated=st.text_area('Text used for matching',st.session_state.resume,height=360)
            if st.button('Save corrected text'):
                st.session_state.resume=updated;(DATA/'resume_text.txt').write_text(updated,encoding='utf-8');st.success('Saved.')
    st.caption('Scanned image-only PDFs require OCR and are not supported by the current parser.')

elif page=='⚙️ Sources & settings':
    st.title('⚙️ Sources & settings')
    st.write('Live public feed integrations are available without an OpenAI key. Employer boards are optional.')
    boards=safe_json('boards.json',{'greenhouse':[],'lever':[]})
    with st.form('boards'):
        gh=st.text_area('Greenhouse employer board tokens (one per line)', '\n'.join(boards.get('greenhouse',[])))
        lv=st.text_area('Lever employer board tokens (one per line)', '\n'.join(boards.get('lever',[])))
        if st.form_submit_button('Save job sources'):
            boards={'greenhouse':[x.strip() for x in gh.splitlines() if x.strip()],'lever':[x.strip() for x in lv.splitlines() if x.strip()]}
            (ROOT/'boards.json').write_text(json.dumps(boards,indent=2),encoding='utf-8');st.success('Saved.')
    st.warning('This build is search-and-match only. No background automation, email sending, or ATS submission is enabled in the new interface.')

elif page=='🛡️ Guarded applications':
    st.title('🛡️ Guarded applications')
    st.write('80% minimum · 5 applications/day · verified recruiter email or authorized ATS only.')
    st.warning('Preparation mode: this page does NOT send emails or submit ATS forms. A score alone never establishes mandatory eligibility.')
    profile=safe_json('profile.json',{})
    contacts=safe_json('approved_contacts.json',{})
    st.info('Before preparing a job-specific résumé, review the original résumé and manually confirm mandatory requirements for that job.')
    db=init_actions(DATA/'applications_queue.db')
    records=pd.read_sql_query('SELECT title,company,score,eligibility,route,status,reason,created_at FROM application_queue ORDER BY created_at DESC',db)
    if len(records):
        st.dataframe(records,hide_index=True,use_container_width=True)
        st.download_button('Export application queue',records.to_csv(index=False).encode('utf-8-sig'),'application_queue.csv','text/csv')
    else:st.caption('No applications prepared yet. Search jobs, then use Prepare application on a matching vacancy.')
    db.close()

elif page=='⭐ Saved & tracked jobs':
    st.title('⭐ Saved & tracked jobs')
    db=connect(DATA/'autojob_website.db')
    df=pd.read_sql_query('SELECT title,company,source,location,match_score,status,url,seen_at FROM jobs ORDER BY match_score DESC,seen_at DESC',db)
    if df.empty:st.info('Find jobs first; discoveries will be recorded here.')
    else:
        selected=st.selectbox('Status filter',['All','saved','applied','discovered','ignored'])
        if selected!='All':df=df[df.status==selected]
        st.dataframe(df,hide_index=True,use_container_width=True,column_config={'url':st.column_config.LinkColumn('Application page')})
        st.download_button('Download tracking CSV',df.to_csv(index=False).encode('utf-8-sig'),'autojob_tracker.csv','text/csv')
    db.close()

else:
    st.markdown('<div class="brand">Find jobs that match your résumé</div><p class="intro">Search real listings, compare requirements, and apply through the original employer website.</p>',unsafe_allow_html=True)
    uploaded=st.file_uploader('Upload your résumé (PDF / DOCX / TXT)',type=['pdf','docx','txt'],help='Stored locally. Do not upload credentials or sensitive IDs.')
    if uploaded:
        try:
            if st.session_state.get('uploaded_name')!=uploaded.name or not st.session_state.resume:
                st.session_state.resume=save_resume(uploaded);st.session_state.uploaded_name=uploaded.name
            st.success(f'Résumé ready — {len(st.session_state.resume.split())} words extracted')
        except Exception as e:st.error(str(e))
    elif st.session_state.resume:st.caption(f'✓ Saved résumé loaded — {len(st.session_state.resume.split())} words')
    a,b,c=st.columns([3,2,1])
    with a: query=st.text_input('Job title or keyword',value='financial analyst',placeholder='e.g. financial analyst, data analyst')
    with b:loc=st.selectbox('Location',['India + worldwide remote','India only (approximate)','All locations'],index=0)
    with c: threshold=st.number_input('Minimum match %',0,100,45,5)
    st.caption('Location restrictions differ across job sources. Always verify eligibility on the employer page.')
    if st.button('🔍 Search matching jobs',type='primary',use_container_width=True):
        if not st.session_state.resume.strip():st.error('Upload a résumé first.')
        elif not query.strip():st.error('Enter a job title or keyword.')
        else:
            with st.spinner('Searching public feeds and ranking jobs...'):
                boards=safe_json('boards.json',{'greenhouse':[],'lever':[]})
                policy='all' if loc=='All locations' else 'india_remote'
                jobs,errors=fetch_public(query.strip(),boards,location_policy=policy)
                if loc=='India only (approximate)':
                    from live_sources import INDIA
                    jobs=[j for j in jobs if any(token in j['location'].lower() for token in INDIA)]
                for j in jobs:j.update(score(st.session_state.resume,j))
                st.session_state.jobs=sorted(jobs,key=lambda j:j['match_score'],reverse=True)
                st.session_state.errors=errors
                db=connect(DATA/'autojob_website.db');upsert(db,st.session_state.jobs);db.close()
    st.markdown('**Search LinkedIn, Indeed and Naukri directly**')
    links=portals(query,'India')
    st.markdown(' · '.join(f'[{name} ↗]({url})' for name,url in links.items()))
    st.caption('These open native search pages. Their individual listings are not included in the API-match count below.')
    jobs=st.session_state.jobs; filtered=[j for j in jobs if j['match_score']>=threshold]
    k1,k2,k3=st.columns(3)
    k1.metric('Jobs fetched',len(jobs));k2.metric('Matching jobs',len(filtered));k3.metric('Feed errors',len(st.session_state.errors))
    for e in st.session_state.errors:st.warning(e)
    if not jobs:st.info('Upload a résumé and click Search matching jobs to retrieve live vacancies. Results will appear here.')
    else:
        sources=sorted({j['source'] for j in filtered})
        selection=st.multiselect('Filter by job source',sources,default=sources)
        filtered=[j for j in filtered if j['source'] in selection]
        if not filtered:st.info('No jobs meet the current filter. Lower the threshold or try a broader query.')
        else:
            export=pd.DataFrame([{k:j.get(k,'') for k in ('title','company','location','source','match_score','url','skills_matched','skills_missing')} for j in filtered])
            st.download_button('Download matching jobs CSV',export.to_csv(index=False).encode('utf-8-sig'),'matching_jobs.csv','text/csv')
            st.caption('Scores are similarity estimates, not verified eligibility. The guarded application minimum is 80%, with separate mandatory checks.')
            db=connect(DATA/'autojob_website.db')
            for j in filtered[:100]:
                with st.container(border=True):
                    left,right=st.columns([4,1])
                    with left:
                        st.markdown(f'#### {j["title"]}')
                        st.markdown(f'<span class="jobmeta">{j["company"]} · {j["location"]} · {j["source"]}</span>',unsafe_allow_html=True)
                        if j['skills_matched']:st.caption('Matching skills: '+', '.join(j['skills_matched'][:12]))
                        if j['skills_missing']:st.caption('Mentioned in job, not detected in résumé: '+', '.join(j['skills_missing'][:9]))
                    with right:
                        st.metric('Similarity',f'{j["match_score"]}%')
                        st.link_button('View / Apply ↗',j['url'],use_container_width=True)
                        if st.button('⭐ Save',key='save_'+j['job_id'],use_container_width=True):
                            set_status(db,j['job_id'],'saved');st.toast('Saved to your tracker')
                    if j['match_score'] >= 80:
                        with st.expander('🛡️ Prepare tailored application (review only)'):
                            st.caption('Review the job description before confirming mandatory requirements. Unverified criteria must NOT be marked met.')
                            confirmed=st.checkbox('I reviewed the job posting and confirm ALL mandatory criteria are supported by my original résumé.',key='req_'+j['job_id'])
                            profile_verified=st.checkbox('I verified the extracted candidate résumé against the original document.',key='prof_'+j['job_id'])
                            config=safe_json('approved_contacts.json',{})
                            rec=verified_email(config,j)
                            route='email' if rec else 'ats_review'
                            state=gate(j['match_score'],'met' if confirmed else 'unknown',profile_verified,route,contact_verified=bool(rec))
                            if state['reasons']:st.warning('; '.join(state['reasons']))
                            else:st.success('Ready for preparation — not yet sent or submitted')
                            if st.button('Generate truthful tailored PDF + queue',key='prepare_'+j['job_id'],disabled=not state['ready']):
                                item=dict(j)
                                if not safe_employer_url(item.get('url','')):st.error('Official HTTPS job URL is required.')
                                else:
                                    try:
                                        name=safe_json('profile.json',{}).get('full_name','Candidate')
                                        pdf=create_tailored_pdf(st.session_state.resume,item,DATA/'tailored_resumes',name)
                                        queue=init_actions(DATA/'applications_queue.db')
                                        queue_application(queue,item,j['match_score'],'met',route,'ready_for_review','No external action has occurred',pdf,rec or '')
                                        queue.close()
                                        st.success('Created and queued locally — not sent.')
                                        st.download_button('Download tailored PDF',data=pdf.read_bytes(),file_name=pdf.name,mime='application/pdf',key='download_'+j['job_id'])
                                        if rec:
                                            email=draft_email(item,name,rec)
                                            st.write('**Proposed email to verified contact:** '+rec)
                                            st.text_area('Email preview',email['subject']+'\n\n'+email['body'],height=180,key='emailpreview_'+j['job_id'])
                                    except Exception as exc:st.error(f'Preparation failed: {type(exc).__name__}: {exc}')
                    with st.expander('Job description & match details'):
                        st.write(j['description'][:4500] or 'Description not supplied by source.')
                        st.info(j['reason'])
            db.close()
    st.caption('Job content attribution: Himalayas (himalayas.app), Remotive (remotive.com), Greenhouse and Lever employer boards.')
