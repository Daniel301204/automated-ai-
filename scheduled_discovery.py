"""Discover jobs for opted-in users. This process cannot send applications."""
import json
import os
from sqlalchemy import select
from live_sources import fetch_public, location_assessment
from resume_match import score
from workflow import Store
from loops import discover_loop


def run(store, fetcher=fetch_public):
    with store.engine.connect() as conn:
        users = list(conn.execute(select(store.users.c.tenant, store.users.c.profile, store.users.c.resume_text)).mappings())
    failures = 0
    for user in users:
        profile = json.loads(user['profile'])
        saved_loops = store.list_loops(user['tenant'])
        if saved_loops:
            for loop in saved_loops:
                if not loop['enabled'] or not user['resume_text']:
                    continue
                try:
                    config = json.loads(loop['config'])
                    jobs, errors = discover_loop(config, user['resume_text'], fetcher)
                    for job in jobs:
                        job.update(loop_id=loop['loop_id'], loop_threshold=config['threshold'], loop_limit=config['daily_limit'], email_subject=config['subject'], email_body=config['body'])
                    store.remember(user['tenant'], jobs)
                    failures += bool(errors)
                    print(f'Loop discovery completed: {len(jobs)} listings, {len(errors)} source errors. No applications sent.')
                except Exception:
                    failures += 1
                    print('Loop discovery failed; saved records preserved. No applications sent.')
            continue
        if not profile.get('agent_enabled') or not user['resume_text']:
            continue
        try:
            jobs, errors = fetcher(profile.get('query', ''), profile.get('boards', {}),
                location_policy='all' if profile.get('location') == 'All locations' else 'india_remote')
            if profile.get('location') == 'India only':
                jobs = [job for job in jobs if location_assessment(job['location']) == 'India listed']
            for job in jobs:
                job.update(score(user['resume_text'], job))
            store.remember(user['tenant'], jobs)
            if errors:
                failures += 1
            print(f'Discovery completed: {len(jobs)} listings, {len(errors)} source errors. No applications sent.')
        except Exception:
            failures += 1
            print('Discovery failed for a workspace; saved records preserved. No applications sent.')
    return failures


if __name__ == '__main__':
    url = os.environ.get('AUTOJOB_DATABASE_URL')
    if not url or not url.startswith('postgresql+psycopg://'):
        raise SystemExit('Configure AUTOJOB_DATABASE_URL for PostgreSQL before scheduling.')
    raise SystemExit(1 if run(Store(url)) else 0)
