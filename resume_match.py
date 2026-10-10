"""Local resume extraction and transparent lexical ranking; no API key required."""
from __future__ import annotations
import io,re,math
from collections import Counter

STOP=set('the and for with are you your our this that have has will from they them work team role position about who where what when able within into more than using use used across strong good excellent including through plus based should must preferred required years year experience skills responsibilities requirements opportunity company job looking working highly ability'.split())
SKILLS=['python','sql','excel','power bi','tableau','machine learning','statistics','financial modeling','financial modelling','risk management','portfolio management','asset management','investment banking','equity research','data analysis','data analytics','financial analysis','accounting','budgeting','forecasting','pandas','numpy','scikit-learn','pytorch','tensorflow','aws','azure','java','javascript','react','typescript','docker','api','streamlit','data visualization','communication','leadership','credit analysis','valuation','econometrics','r','git','etl','postgresql','mysql','business analysis','derivatives','quantitative finance','fixed income']

def read_resume(filename,raw):
    ext=filename.lower().rsplit('.',1)[-1]
    if ext=='txt': return raw.decode('utf-8-sig',errors='replace')
    if ext=='pdf':
        from pypdf import PdfReader
        reader=PdfReader(io.BytesIO(raw))
        return '\n'.join(page.extract_text() or '' for page in reader.pages)
    if ext=='docx':
        from docx import Document
        return '\n'.join(p.text for p in Document(io.BytesIO(raw)).paragraphs)
    raise ValueError('Upload a PDF, DOCX or TXT résumé')

def terms(s):
    return {x for x in re.findall(r'[a-z][a-z0-9+#.\-]{1,}',s.lower()) if x not in STOP and len(x)>2}

def skills_in(s):
    lowered=' '+re.sub(r'\s+',' ',s.lower())+' '
    return {x for x in SKILLS if re.search(r'(?<![a-z])'+re.escape(x)+r'(?![a-z])',lowered)}

def score(resume,job):
    jd=' '.join([job.get('title',''),job.get('description','')]); rt=terms(resume); jt=terms(jd)
    rs=skills_in(resume); js=skills_in(jd)
    overlap=rt&jt; common=rs&js
    keyword_score=len(overlap)/max(1,min(len(jt),45))
    skill_score=(len(common)/len(js)) if js else keyword_score
    title_terms=terms(job.get('title',''))
    role_score=len(title_terms&rt)/max(1,len(title_terms))
    value=round(100*(0.50*skill_score+0.32*min(1,keyword_score*1.8)+0.18*role_score))
    return {'match_score':max(0,min(100,value)), 'skills_matched':sorted(common),'skills_missing':sorted(js-rs),'shared_keywords':sorted(overlap)[:18], 'eligibility':'Review required', 'reason':'Similarity ranking only; experience, work authorization and mandatory eligibility must be verified before applying.'}
