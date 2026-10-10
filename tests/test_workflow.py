import hashlib
import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest
from sqlalchemy import select
from workflow import Store, approval_digest, evidence_profile, send_gmail
from live_sources import fetch_public, location_assessment


@pytest.fixture
def store(tmp_path):
    value = Store('sqlite:///' + str(tmp_path / 'test.db'))
    for tenant in ('alice', 'bob'):
        value.ensure_user(tenant)
        value.save_profile(tenant, resume_text='Verified resume evidence', profile=json.dumps({'threshold': 80, 'daily_limit': 2}))
    return value


def prepared(store, tenant='alice', job_id='job1'):
    job = dict(job_id=job_id, title='Verified resume evidence', company='Employer', match_score=90,
               url='https://example.org/job', description='Verified resume evidence')
    store.remember(tenant, [job])
    app = dict(to='jobs@example.org', subject='Application', body='Reviewed message',
               requirements_verified=True, profile_verified=True, contact_verified=True, score=90,
               resume_digest=hashlib.sha256(b'Verified resume evidence').hexdigest())
    pdf = b'%PDF-test-fixture'
    store.save_profile(tenant, resume=pdf)
    store.prepare(tenant, job_id, app, pdf)
    return approval_digest(app['to'], app['subject'], app['body'], pdf)


def test_tenant_isolation(store):
    prepared(store)
    assert store.list_jobs('bob') == []
    assert store.profile('bob')['resume_text'] == 'Verified resume evidence'
    with pytest.raises(Exception):
        store.prepare('bob', 'job1', {}, b'%PDF-fixture')
    assert store.list_jobs('alice')[0]['status'] == 'needs_review'


def test_send_requires_exact_approval_and_is_not_duplicated(store):
    digest = prepared(store)
    sender = Mock(return_value='gmail-id')
    with pytest.raises(ValueError, match='Approval'):
        store.send_approved('alice', 'job1', 'wrong-digest', {}, sender=sender)
    sender.assert_not_called()
    assert store.send_approved('alice', 'job1', digest, {}, sender=sender) == 'gmail-id'
    assert store.list_jobs('alice')[0]['status'] == 'awaiting_response'
    with pytest.raises(ValueError):
        store.send_approved('alice', 'job1', digest, {}, sender=sender)
    sender.assert_called_once()


def test_uncertain_delivery_never_retries(store):
    digest = prepared(store)
    sender = Mock(side_effect=TimeoutError('sensitive provider details'))
    with pytest.raises(RuntimeError, match='Check Gmail Sent'):
        store.send_approved('alice', 'job1', digest, {}, sender=sender)
    assert store.list_jobs('alice')[0]['status'] == 'delivery_unknown'
    with pytest.raises(ValueError):
        store.send_approved('alice', 'job1', digest, {}, sender=sender)
    with pytest.raises(ValueError):
        store.track('alice', 'job1', 'needs_review')
    with pytest.raises(ValueError):
        prepared(store)
    sender.assert_called_once()


def test_daily_limit_is_per_user_and_persisted(store):
    sender = Mock(return_value='gmail-id')
    for index in range(2):
        job_id = str(index)
        digest = prepared(store, job_id=job_id)
        store.send_approved('alice', job_id, digest, {}, sender=sender)
    digest = prepared(store, job_id='third')
    with pytest.raises(ValueError, match='limit'):
        store.send_approved('alice', 'third', digest, {}, sender=sender)
    digest = prepared(store, tenant='bob')
    store.send_approved('bob', 'job1', digest, {}, sender=sender)
    assert sender.call_count == 3


def test_resume_change_invalidates_approval(store):
    digest = prepared(store)
    store.save_profile('alice', resume_text='New evidence')
    sender = Mock()
    with pytest.raises(ValueError, match='changed'):
        store.send_approved('alice', 'job1', digest, {}, sender=sender)
    sender.assert_not_called()


def test_remember_preserves_application_status(store):
    digest = prepared(store)
    store.send_approved('alice', 'job1', digest, {}, sender=Mock(return_value='sent'))
    store.remember('alice', [dict(job_id='job1', title='Updated title')])
    assert store.list_jobs('alice')[0]['status'] == 'awaiting_response'
    with pytest.raises(ValueError):
        store.track('alice', 'job1', 'needs_review')


def test_evidence_is_literal_and_does_not_invent_experience():
    text = 'MSc Finance at University\nIntern, Example 2024\nPython and SQL'
    profile = evidence_profile(text)
    assert profile['education_evidence'] == ['MSc Finance at University']
    assert profile['experience_evidence'] == ['Intern, Example 2024']
    assert profile['skills'] == ['python', 'sql']
    assert 'experience_years' not in profile


def test_provider_send_uses_https_without_retry():
    session = Mock()
    token, sent = Mock(), Mock()
    token.json.return_value = {'access_token': 'fake-test-token'}
    sent.json.return_value = {'id': 'test-message'}
    session.post.side_effect = [token, sent]
    assert send_gmail(dict(client_id='fake', client_secret='fake', refresh_token='fake', sender_email='alice@example.org'),
        'jobs@example.org', 'Subject', 'Body', b'%PDF-test', session) == 'test-message'
    assert session.post.call_count == 2
    assert session.post.call_args_list[1].args[0] == 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send'
    with pytest.raises(ValueError):
        send_gmail({}, 'a@example.org,b@example.org', 'Subject', 'Body', b'', session)
    assert session.post.call_count == 2


def test_local_keyword_filter_and_feed_failure_isolation():
    session = Mock()
    himalayas, remotive = Mock(), Mock()
    himalayas.json.return_value = {'jobs': [dict(title='Unrelated writer', location='India', applicationLink='https://example.org/1'),
        dict(title='Financial analyst', location='India', applicationLink='https://example.org/2', description='Financial analyst') ]}
    remotive.raise_for_status.side_effect = ValueError('invalid provider response')
    session.get.side_effect = [himalayas, remotive]
    jobs, errors = fetch_public('financial analyst', {}, session=session)
    assert len(jobs) == 1 and jobs[0]['title'] == 'Financial analyst'
    assert len(errors) == 1 and errors[0].startswith('Remotive:')
    assert location_assessment('Remote') == 'Eligibility unverified'
    assert location_assessment('Indiana, USA') == 'Other region listed'


def test_hosted_app_does_not_expose_data_without_configuration(monkeypatch):
    monkeypatch.delenv('AUTOJOB_LOCAL_DEV', raising=False)
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / 'streamlit_app.py').run(timeout=20)
    assert not app.exception
    assert 'setup' in app.title[0].value.lower()
    assert not app.get('file_uploader')


def test_all_pages_render_in_explicit_local_mode(monkeypatch, tmp_path):
    monkeypatch.setenv('AUTOJOB_LOCAL_DEV', '1')
    monkeypatch.setenv('AUTOJOB_DATABASE_URL', 'sqlite:///' + str(tmp_path / 'ui.db'))
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / 'streamlit_app.py').run(timeout=20)
    for page in ['Find jobs', 'My résumé', 'Settings', 'Review & approve', 'Tracking']:
        app.sidebar.radio[0].set_value(page).run(timeout=20)
        assert not app.exception, (page, app.exception)


@pytest.mark.skipif(not os.getenv('AUTOJOB_TEST_POSTGRES_URL'), reason='Dedicated PostgreSQL test database not supplied')
def test_postgres_concurrent_approval_is_single_send():
    import uuid
    value = Store(os.environ['AUTOJOB_TEST_POSTGRES_URL'])
    tenant = 'test-' + uuid.uuid4().hex
    value.ensure_user(tenant)
    value.save_profile(tenant, resume_text='Verified resume evidence', profile='{}')
    digest = prepared(value, tenant=tenant)
    sender = Mock(return_value='test-message')
    def attempt():
        try:
            return value.send_approved(tenant, 'job1', digest, {}, sender=sender)
        except ValueError:
            return 'blocked'
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: attempt(), range(2)))
        assert sorted(results) == ['blocked', 'test-message']
        sender.assert_called_once()
    finally:
        with value.engine.begin() as conn:
            conn.execute(value.jobs.delete().where(value.jobs.c.tenant == tenant))
            conn.execute(value.users.delete().where(value.users.c.tenant == tenant))


def test_scheduler_only_discovers_opted_in_users(store):
    from scheduled_discovery import run
    store.save_profile('alice', profile=json.dumps({'agent_enabled': True, 'query': 'analyst', 'location': 'India only'}))
    fetcher = Mock(return_value=([dict(job_id='scheduled',title='Analyst',company='Example',location='India',description='Verified resume evidence')], []))
    assert run(store, fetcher) == 0
    fetcher.assert_called_once()
    assert store.list_jobs('alice')[0]['status'] == 'discovered'
    assert store.list_jobs('bob') == []


@pytest.mark.skipif(not os.getenv('AUTOJOB_TEST_POSTGRES_URL'), reason='Dedicated PostgreSQL test database not supplied')
def test_gmail_oauth_is_user_bound_encrypted_and_one_use():
    import uuid
    from urllib.parse import urlparse, parse_qs
    from cryptography.fernet import Fernet
    from gmail_connection import GmailConnections
    value = Store(os.environ['AUTOJOB_TEST_POSTGRES_URL'])
    tenant = 'oauth-test-' + uuid.uuid4().hex
    other = 'other-' + uuid.uuid4().hex
    connections = GmailConnections(value.engine, dict(client_id='fake-client', client_secret='fake-secret', redirect_uri='https://example.org/'), Fernet.generate_key().decode())
    try:
        url = connections.authorize_url(tenant, 'alice@example.org')
        state = parse_qs(urlparse(url).query)['state'][0]
        session = Mock()
        response = Mock()
        response.json.return_value = dict(id_token='fake-id', refresh_token='fake-refresh', scope='openid email https://www.googleapis.com/auth/gmail.send')
        session.post.return_value = response
        verifier = Mock(return_value=dict(email='alice@example.org', email_verified=True))
        with pytest.raises(ValueError, match='state'):
            connections.finish(other, 'alice@example.org', state, 'fake-code', session, verifier)
        session.post.assert_not_called()
        connections.finish(tenant, 'alice@example.org', state, 'fake-code', session, verifier)
        assert connections.credentials(tenant)['refresh_token'] == 'fake-refresh'
        assert connections.credentials(other) is None
        with value.engine.connect() as conn:
            stored = conn.execute(select(connections.table.c.token).where(connections.table.c.tenant == tenant)).scalar_one()
        assert stored != 'fake-refresh'
        with pytest.raises(ValueError, match='state'):
            connections.finish(tenant, 'alice@example.org', state, 'fake-code', session, verifier)
        session.post.assert_called_once()
        connections.disconnect(tenant)
        assert connections.credentials(tenant) is None
        state = parse_qs(urlparse(connections.authorize_url(tenant, 'alice@example.org')).query)['state'][0]
        verifier.return_value = dict(email='bob@example.org', email_verified=True)
        with pytest.raises(ValueError, match='same verified email'):
            connections.finish(tenant, 'alice@example.org', state, 'fake-code', session, verifier)
        assert connections.credentials(tenant) is None
    finally:
        with value.engine.begin() as conn:
            conn.execute(connections.table.delete().where(connections.table.c.tenant.in_([tenant, other])))


def test_prepared_application_ui_requires_final_approval(monkeypatch, tmp_path):
    url = 'sqlite:///' + str(tmp_path / 'review-ui.db')
    value = Store(url)
    value.ensure_user('local-development')
    value.save_profile('local-development', resume_text='Verified resume evidence', filename='resume.pdf', profile=json.dumps({'name':'Test Candidate','threshold':80}))
    prepared(value, tenant='local-development')
    monkeypatch.setenv('AUTOJOB_LOCAL_DEV', '1')
    monkeypatch.setenv('AUTOJOB_DATABASE_URL', url)
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / 'streamlit_app.py').run(timeout=20)
    app.sidebar.radio[0].set_value('Review & approve').run(timeout=20)
    assert not app.exception
    send = next(b for b in app.button if b.label == 'Approve and send this email')
    assert send.disabled
    assert any('exact email' in c.label for c in app.checkbox)
    assert any('Gmail OAuth' in item.value for item in app.info)
