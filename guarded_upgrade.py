"""Safe, evidence-only application preparation. Does not submit applications."""
from __future__ import annotations
import hashlib, json, re, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

CONFIRMED='met'

def gate(score, mandatory_status, confirmed_profile, destination, contact_verified=False, limit=5, sent_today=0):
    reasons=[]
    if score < 80: reasons.append('Match below 80%')
    if mandatory_status != CONFIRMED: reasons.append('Mandatory job requirements not confirmed')
    if not confirmed_profile: reasons.append('Candidate profile has not been verified')
    if not destination: reasons.append('No application route available')
    if destination == 'email' and not contact_verified: reasons.append('Recruiter/application email not verified')
    if sent_today >= min(5,limit): reasons.append('Daily cap reached')
    return {'ready':not reasons,'reasons':reasons}

def evidence_bullets(resume_text, job_description, maximum=7):
    """Literal, non-generated excerpts from source resume; prioritize overlapping keywords."""
    lines=[re.sub(r'\s+',' ',x).strip(' •-\t') for x in resume_text.splitlines()]
    lines=[x for x in lines if 12<=len(x)<=240 and not re.search(r'(?i)\b(aadhaar|passport number|date of birth)\b',x)]
    needle=set(re.findall(r'[a-z]{4,}',job_description.lower()))
    ranked=sorted(enumerate(lines),key=lambda it:(-len(set(re.findall(r'[a-z]{4,}',it[1].lower())) & needle),it[0]))
    return [x for _,x in ranked[:maximum]]

def create_tailored_pdf(resume_text, job, output_dir, candidate_name='Candidate'):
    if not resume_text or len(resume_text.strip())<45: raise ValueError('Verified resume text is required')
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True)
    fingerprint=hashlib.sha256((job['job_id']+resume_text).encode()).hexdigest()[:16]
    path=output_dir/f'tailored_{fingerprint}.pdf'
    c=canvas.Canvas(str(path),pagesize=A4)
    width,height=A4; y=height-54
    def line(content, size=10, bold=False):
        nonlocal y
        font='Helvetica-Bold' if bold else 'Helvetica'
        c.setFont(font,size)
        clean=content.encode('latin-1','replace').decode('latin-1')
        for piece in simpleSplit(clean,font,size,width-95):
            if y<52: c.showPage(); y=height-52;c.setFont(font,size)
            c.drawString(45,y,piece);y-=size+5
    line(candidate_name,17,True)
    line('Relevant evidence from original resume',11,True)
    line('Position: '+str(job.get('title','')),9)
    y-=12
    for bullet in evidence_bullets(resume_text,job.get('description','')): line('• '+bullet)
    y-=15
    line('Source: candidate-provided resume. No qualifications were generated.',8)
    c.save()
    return path

def verified_email(contacts, job):
    # Manually verified mapping; no guessing / email discovery by LLM.
    key=job.get('company_key') or job.get('company','')
    v=contacts.get(key,{})
    addr=v.get('email','').strip()
    if v.get('verified') is True and re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',addr):return addr
    return None

def draft_email(job, name, recipient):
    return {'to':recipient,'subject':f'Application for {job.get("title", "open position")} — {name}',
        'body':f'Dear Hiring Team,\n\nI am applying for the {job.get("title", "position")} role at {job.get("company", "your company")}. Please find my résumé attached for your consideration.\n\nOfficial vacancy: {job.get("url", "")}\n\nKind regards,\n{name}'}

def init_actions(db_path):
    db=sqlite3.connect(db_path)
    db.execute('''CREATE TABLE IF NOT EXISTS application_queue (job_id TEXT PRIMARY KEY, title TEXT, company TEXT, score INTEGER, eligibility TEXT, route TEXT, status TEXT, reason TEXT, tailored_pdf TEXT, recipient TEXT, created_at TEXT)''')
    db.commit()
    return db

def queue_application(db,job,score,eligibility,route,status,reason,pdf='',recipient=''):
    values=(job['job_id'],job['title'],job['company'],score,eligibility,route,status,reason,str(pdf),recipient,datetime.now(timezone.utc).isoformat())
    db.execute('''INSERT INTO application_queue VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(job_id) DO UPDATE SET score=excluded.score,eligibility=excluded.eligibility,route=excluded.route,status=CASE WHEN application_queue.status IN ('sent','submitted') THEN application_queue.status ELSE excluded.status END,reason=excluded.reason,tailored_pdf=excluded.tailored_pdf,recipient=excluded.recipient''',values)
    db.commit()

def safe_employer_url(url):
    parsed=urlparse(url)
    return parsed.scheme=='https' and bool(parsed.netloc) and not parsed.username and not parsed.password
