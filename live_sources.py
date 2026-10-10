"""Live public job feeds. Read-only; no scraping, login, or application submission."""
from __future__ import annotations
import re
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

HEADERS = {'User-Agent': 'AutoJobAI/2.1 (personal job search; read-only)'}
INDIA = ('india', 'bengaluru', 'bangalore', 'hyderabad', 'chennai', 'mumbai', 'pune', 'delhi', 'gurgaon', 'gurugram', 'noida', 'kolkata', 'kochi', 'ahmedabad', 'jaipur', 'remote - india', 'remote india')

def text(v):
    return BeautifulSoup(str(v or ''), 'html.parser').get_text(' ', strip=True)[:16000]

def location_assessment(location, worldwide=False):
    """Three-valued location check; never infer India eligibility from 'remote' alone."""
    s = str(location or '').lower().strip()
    restricted = ('united states', 'usa', 'us only', 'canada', 'uk only',
                  'united kingdom', 'europe only', 'eu only', 'australia only')
    india = any(re.search(r'(?<![a-z])'+re.escape(x)+r'(?![a-z])',s) for x in INDIA)
    if india: return 'India listed'
    if worldwide or any(x in s for x in ('worldwide','anywhere in the world','globally','global remote')):
        return 'Worldwide listed'
    if any(x in s for x in restricted): return 'Other region listed'
    return 'Eligibility unverified'

def good_location(location, policy='india_remote', worldwide=False):
    if policy=='all': return True
    return location_assessment(location, worldwide) in ('India listed','Worldwide listed')

def portals(query, location='India'):
    q, loc = quote_plus(query or 'jobs'), quote_plus(location or 'India')
    return {
       'LinkedIn': f'https://www.linkedin.com/jobs/search/?keywords={q}&location={loc}',
       'Indeed': f'https://in.indeed.com/jobs?q={q}&l={loc}',
       'Naukri': f'https://www.naukri.com/{(query or "jobs").strip().lower().replace(" ", "-")}-jobs',
    }

def _get_json(session,url,params=None):
    r = session.get(url, params=params, timeout=18, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def fetch_public(query, boards=None, session=None, per_source=50, location_policy='india_remote'):
    """Return (list[normalized job], list[readable source errors])."""
    session = session or requests.Session()
    jobs, errors = [], []
    try:
        payload=_get_json(session,'https://himalayas.app/jobs/api/search',{'q':query,'sort':'recent','page':1})
        for j in payload.get('jobs', [])[:per_source]:
            restriction=j.get('locationRestrictions') or j.get('location') or []
            if isinstance(restriction,list): restriction=', '.join(str(x.get('name',x) if isinstance(x,dict) else x) for x in restriction)
            location=restriction or ('Worldwide remote' if j.get('worldwide') else 'Remote — check location restrictions')
            if good_location(location,location_policy,j.get('worldwide',False)):
                url=j.get('applicationLink') or j.get('url') or j.get('guid') or ''
                if str(url).startswith('https://'):
                    jobs.append(dict(job_id='himalayas:'+str(j.get('guid') or j.get('id') or url), title=j.get('title',''), company=j.get('companyName',''), location=location, source='Himalayas', url=url, description=text(j.get('description')), location_status=location_assessment(location,j.get('worldwide',False)), posted=str(j.get('pubDate',''))))
    except (requests.RequestException,ValueError,TypeError,AttributeError) as e:
        errors.append('Himalayas: '+str(e)[:180])
    try:
        payload=_get_json(session,'https://remotive.com/api/remote-jobs',{'search':query,'limit':per_source})
        for j in payload.get('jobs',[])[:per_source]:
            location=j.get('candidate_required_location','Worldwide remote')
            if good_location(location,location_policy):
                url=j.get('url','')
                if str(url).startswith('https://'):
                    jobs.append(dict(job_id='remotive:'+str(j.get('id',url)),title=j.get('title',''),company=j.get('company_name',''),location=location, source='Remotive',url=url,description=text(j.get('description')),location_status=location_assessment(location),posted=str(j.get('publication_date',''))))
    except (requests.RequestException, ValueError,TypeError,AttributeError) as e:
        errors.append('Remotive: '+str(e)[:180])
    for source in ('greenhouse','lever'):
        for board in (boards or {}).get(source,[]):
            if not isinstance(board,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',board):
                errors.append(f'{source}: invalid board token'); continue
            url = f'https://boards-api.greenhouse.io/v1/boards/{board}/jobs' if source=='greenhouse' else f'https://api.lever.co/v0/postings/{board}'
            try:
                payload=_get_json(session,url, {'content':'true'} if source=='greenhouse' else {'mode':'json'})
                records=payload.get('jobs',[]) if source=='greenhouse' else payload
                for j in records:
                    if source=='greenhouse':
                        location=(j.get('location') or {}).get('name','')
                        title=j.get('title',''); link=j.get('absolute_url',''); desc=text(j.get('content'))
                    else:
                        location=(j.get('categories') or {}).get('location','')
                        title=j.get('text','');link=j.get('hostedUrl','');desc=text(j.get('descriptionPlain') or j.get('description'))
                    if not link.startswith('https://') or not good_location(location,location_policy): continue
                    jobs.append(dict(job_id=f'{source}:{board}:{j.get("id",link)}', title=title,company=board,location=location,source=source.title(),url=link,description=desc,posted=''))
            except (requests.RequestException,ValueError,TypeError,AttributeError) as e:
                errors.append(f'{source}/{board}: {str(e)[:170]}')
    seen={}
    for j in jobs:
        if j['url'] not in seen:
            j.setdefault('location_status', location_assessment(j.get('location','')))
            seen[j['url']]=j
    return list(seen.values()),errors
