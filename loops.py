"""Validated search loops, evidence-based matching and reviewed email templates."""
import re
from string import Formatter
from live_sources import fetch_public, location_assessment
from resume_match import score

SOURCES = ['Himalayas', 'Remotive', 'Greenhouse', 'Lever']
LOCATIONS = ['India + worldwide remote', 'India only', 'All locations']
SUBJECT = 'Application for {job_title} — {name}'
BODY = 'Dear Hiring Team,\n\nI would like to apply for the {job_title} role at {company}. Please find my résumé attached for your review.\n\nVacancy: {job_url}\n\nKind regards,\n{name}'


def validate_template(template):
    if not template.strip():
        raise ValueError('An email subject and message are required')
    try:
        for _, field, spec, conversion in Formatter().parse(template):
            if field is not None and (field not in {'job_title', 'company', 'name', 'job_url'} or spec or conversion):
                raise ValueError('Use only {job_title}, {company}, {name} and {job_url} placeholders')
    except ValueError as exc:
        raise ValueError('Invalid email template: ' + str(exc)) from None
    return template


def normalize_loop(config):
    config = dict(config)
    query = str(config.get('query', '')).strip()
    if not query or len(query) > 160:
        raise ValueError('Enter a job title or keyword (up to 160 characters)')
    config['query'] = query
    config['name'] = str(config.get('name') or query).strip()[:100]
    if config.get('location') not in LOCATIONS:
        raise ValueError('Select a supported location policy')
    if not config.get('sources') or any(s not in SOURCES for s in config['sources']):
        raise ValueError('Select at least one supported job source')
    if not 80 <= int(config.get('threshold', 80)) <= 100:
        raise ValueError('Application threshold must be 80–100%')
    if not 1 <= int(config.get('daily_limit', 3)) <= 5:
        raise ValueError('Daily application limit must be 1–5')
    config['threshold'] = int(config.get('threshold', 80))
    config['daily_limit'] = int(config.get('daily_limit', 3))
    for source, tokens in config.get('boards', {}).items():
        if source not in ('greenhouse', 'lever') or len(tokens) > 10 or any(not re.fullmatch(r'[A-Za-z0-9_-]+', t) for t in tokens):
            raise ValueError('Use up to 10 valid employer board tokens per provider')
    config['subject'] = validate_template(config.get('subject', SUBJECT))
    if '\r' in config['subject'] or '\n' in config['subject']:
        raise ValueError('Email subjects cannot contain line breaks')
    config['body'] = validate_template(config.get('body', BODY))
    config['remote_only'] = bool(config.get('remote_only', False))
    return config


def email_preview(config, job, name):
    values = dict(job_title=job['title'], company=job['company'], name=name, job_url=job['url'])
    return validate_template(config.get('subject', SUBJECT)).format(**values), validate_template(config.get('body', BODY)).format(**values)


def discover_loop(config, resume_text, fetcher=fetch_public):
    config = normalize_loop(config)
    jobs, errors = fetcher(config['query'], config.get('boards', {}),
        location_policy='all' if config['location'] == 'All locations' else 'india_remote',
        enabled_sources=config['sources'])
    if config['location'] == 'India only':
        jobs = [j for j in jobs if location_assessment(j['location']) == 'India listed']
    if config['remote_only']:
        jobs = [j for j in jobs if re.search(r'\b(remote|worldwide|anywhere|globally)\b', j.get('location', ''), re.I)]
    for job in jobs:
        job.update(score(resume_text, job))
    return sorted(jobs, key=lambda j: j['match_score'], reverse=True), errors
