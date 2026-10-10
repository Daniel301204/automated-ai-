"""Read-only job-board discovery. Does not import Google or OpenAI SDKs."""
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER_AGENT = {'User-Agent': 'AutoJobAI/2.0 (public board discovery; no submissions)'}
INDIA_TERMS = ('india', 'bengaluru', 'bangalore', 'hyderabad', 'pune', 'mumbai', 'delhi',
               'noida', 'gurugram', 'gurgaon', 'kolkata', 'chennai', 'ahmedabad', 'kochi',
               'coimbatore', 'jaipur', 'bhubaneswar', 'indore', 'thiruvananthapuram')


def eligible_location(location):
    loc = (location or '').casefold()
    return any(term in loc for term in INDIA_TERMS) or 'remote' in loc or 'work from anywhere' in loc


def _plain(markup):
    return BeautifulSoup(markup or '', 'html.parser').get_text(' ', strip=True)[:12000]


def discover(boards, roles=(), session=None, limit=250):
    """Returns (jobs, errors); partial board failures never hide successful boards."""
    session = session or requests.Session()
    collected, errors = [], []
    for provider in ('greenhouse', 'lever'):
        for token in boards.get(provider, []):
            if not isinstance(token, str) or not re.fullmatch('[A-Za-z0-9_-]+', token):
                errors.append(f'{provider}: invalid board token')
                continue
            url = (f'https://boards-api.greenhouse.io/v1/boards/{token}/jobs' if provider == 'greenhouse'
                   else f'https://api.lever.co/v0/postings/{token}')
            try:
                response = session.get(url, params={'content': 'true'} if provider == 'greenhouse' else {'mode': 'json'},
                                       headers=USER_AGENT, timeout=15)
                response.raise_for_status()
                records = response.json()
                if provider == 'greenhouse':
                    records = records['jobs']
                if not isinstance(records, list):
                    raise ValueError('Unexpected board API response')
                for record in records:
                    if provider == 'greenhouse':
                        location = (record.get('location') or {}).get('name', '')
                        title = record.get('title', '')
                        link = record.get('absolute_url', '')
                        description = _plain(record.get('content', ''))
                    else:
                        location = (record.get('categories') or {}).get('location', '')
                        title = record.get('text', '')
                        link = record.get('hostedUrl', '')
                        description = record.get('descriptionPlain') or _plain(record.get('description'))
                        if not description:
                            description = ' '.join(_plain(v.get('content')) for v in record.get('lists', []))
                    if not eligible_location(location) or not link.startswith('https://'):
                        continue
                    collected.append({'job_id': f'{provider}:{token}:{record["id"]}',
                         'company': token, 'title': title, 'location': location,
                         'source': provider, 'url': link, 'description': description})
            except (requests.RequestException, ValueError, KeyError, TypeError) as ex:
                errors.append(f'{provider}/{token}: {type(ex).__name__}: {str(ex)[:110]}')
    unique = {job['job_id']: job for job in collected}
    role_terms = [str(r).casefold() for r in roles if r]
    jobs = sorted(unique.values(), key=lambda x: (
        not any(role in x['title'].casefold() for role in role_terms), x['company'], x['title']))
    return jobs[:max(0, limit)], errors


def discover_and_save(boards, roles, directory, session=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    jobs, errors = discover(boards, roles, session)
    cols = ['job_id', 'company', 'title', 'location', 'source', 'url', 'description']
    output = directory / 'discovered_jobs.csv'
    temp = directory / 'discovered_jobs.csv.tmp'
    with temp.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=cols)
        writer.writeheader()
        writer.writerows(jobs)
    temp.replace(output)
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'retained': len(jobs),
              'errors': errors, 'sources_configured': {p: len(boards.get(p, [])) for p in ('greenhouse', 'lever')}}
    (directory / 'discovery_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report
