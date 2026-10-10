"""Tenant-isolated persistence and explicit per-message approval. No background sending."""
import base64
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from email.message import EmailMessage

import requests
from sqlalchemy import (create_engine, MetaData, Table, Column, String, Text,
                        LargeBinary, select, update, and_)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import make_url
from resume_match import skills_in


def evidence_profile(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return {
        'skills': sorted(skills_in(text)),
        'education_evidence': [s for s in lines if re.search(r'\b(degree|bachelor|master|university|college|bsc|msc|mba|phd)\b', s, re.I)],
        'experience_evidence': [s for s in lines if re.search(r'\b(experience|worked|analyst|engineer|intern|manager|20\d{2})\b', s, re.I)],
        'preferences': 'Enter your preferences; they cannot be inferred reliably from a résumé.',
    }


def approval_digest(recipient, subject, body, attachment):
    return hashlib.sha256(json.dumps([recipient, subject, body], ensure_ascii=False).encode() + attachment).hexdigest()


def send_gmail(config, recipient, subject, body, attachment, session=None):
    """HTTPS Gmail send, called only after a persistent reservation. Never retries a send."""
    if not re.fullmatch(r'[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+', recipient):
        raise ValueError('A single verified recipient is required')
    if '\r' in subject or '\n' in subject:
        raise ValueError('Invalid subject')
    required = ('client_id', 'client_secret', 'refresh_token', 'sender_email')
    if not all(config.get(k) for k in required):
        raise ValueError('Gmail connection is not configured')
    session = session or requests.Session()
    token = session.post('https://oauth2.googleapis.com/token', data={
        'client_id': config['client_id'], 'client_secret': config['client_secret'],
        'refresh_token': config['refresh_token'], 'grant_type': 'refresh_token'}, timeout=20)
    token.raise_for_status()
    access = token.json()['access_token']
    msg = EmailMessage()
    msg['From'] = config['sender_email']
    msg['To'], msg['Subject'] = recipient, subject
    msg.set_content(body)
    msg.add_attachment(attachment, maintype='application', subtype='pdf', filename='Resume.pdf')
    response = session.post('https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
        headers={'Authorization': 'Bearer ' + access},
        json={'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}, timeout=30)
    response.raise_for_status()
    return response.json()['id']


class Store:
    def __init__(self, url):
        parsed = make_url(url)
        if parsed.get_backend_name() == 'postgresql' and parsed.host not in (None, 'localhost', '127.0.0.1', '::1'):
            # Hosted database connections verify the server's certificate and hostname.
            url = parsed.update_query_dict({'sslmode': 'verify-full', 'sslrootcert': parsed.query.get('sslrootcert', 'system')})
        self.engine = create_engine(url, pool_pre_ping=True)
        metadata = MetaData()
        self.users = Table('autojob_users', metadata,
            Column('tenant', String(64), primary_key=True),
            Column('profile', Text, nullable=False), Column('resume', LargeBinary),
            Column('filename', Text), Column('resume_text', Text))
        self.jobs = Table('autojob_jobs', metadata,
            Column('tenant', String(64), primary_key=True), Column('job_id', String(512), primary_key=True),
            Column('payload', Text, nullable=False), Column('status', String(40), nullable=False),
            Column('application', Text), Column('attachment', LargeBinary),
            Column('reserved_day', String(10)), Column('message_id', Text))
        metadata.create_all(self.engine)

    def ensure_user(self, tenant):
        try:
            with self.engine.begin() as conn:
                if conn.execute(select(self.users.c.tenant).where(self.users.c.tenant == tenant)).first() is None:
                    conn.execute(self.users.insert().values(tenant=tenant, profile='{}'))
        except IntegrityError:
            pass  # A concurrent login inserted this tenant.

    def profile(self, tenant):
        self.ensure_user(tenant)
        with self.engine.connect() as conn:
            return dict(conn.execute(select(self.users).where(self.users.c.tenant == tenant)).mappings().one())

    def save_profile(self, tenant, **values):
        self.ensure_user(tenant)
        with self.engine.begin() as conn:
            conn.execute(update(self.users).where(self.users.c.tenant == tenant).values(**values))

    def remember(self, tenant, jobs):
        if self.engine.dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import insert
        else:
            from sqlalchemy.dialects.sqlite import insert
        with self.engine.begin() as conn:
            for job in jobs:
                statement = insert(self.jobs).values(tenant=tenant, job_id=job['job_id'], payload=json.dumps(job), status='discovered')
                conn.execute(statement.on_conflict_do_update(index_elements=['tenant', 'job_id'], set_={'payload': statement.excluded.payload}))

    def list_jobs(self, tenant):
        with self.engine.connect() as conn:
            columns = [column for column in self.jobs.c if column.name != 'attachment']
            return [dict(r) for r in conn.execute(select(*columns).where(self.jobs.c.tenant == tenant)).mappings()]

    def job(self, tenant, job_id):
        with self.engine.connect() as conn:
            return dict(conn.execute(select(self.jobs).where(and_(self.jobs.c.tenant == tenant, self.jobs.c.job_id == job_id))).mappings().one())

    def prepare(self, tenant, job_id, application, attachment):
        if not attachment.startswith(b'%PDF-'):
            raise ValueError('A reviewed PDF attachment is required')
        with self.engine.begin() as conn:
            key = and_(self.jobs.c.tenant == tenant, self.jobs.c.job_id == job_id)
            row = conn.execute(select(self.jobs).where(key).with_for_update()).mappings().one()
            if row['reserved_day'] or row['status'] in ('submitted', 'awaiting_response', 'interview', 'rejected'):
                raise ValueError('This application has already been dispatched or requires reconciliation')
            conn.execute(update(self.jobs).where(key).values(application=json.dumps(application), attachment=attachment, status='needs_review'))

    def send_approved(self, tenant, job_id, digest, gmail, daily_limit=5, sender=send_gmail):
        if sender is send_gmail and self.engine.dialect.name != 'postgresql':
            raise ValueError('Real email dispatch requires PostgreSQL concurrency protection')
        if not 1 <= daily_limit <= 5:
            raise ValueError('Daily limit must be between 1 and 5')
        day = datetime.now(timezone.utc).date().isoformat()
        # Serializes reservations for a tenant on PostgreSQL; provider call is outside transaction.
        with self.engine.begin() as conn:
            user = conn.execute(select(self.users).where(self.users.c.tenant == tenant).with_for_update()).mappings().one()
            profile = json.loads(user['profile'])
            daily_limit = min(daily_limit, int(profile.get('daily_limit', 5)))
            key = and_(self.jobs.c.tenant == tenant, self.jobs.c.job_id == job_id)
            row = conn.execute(select(self.jobs).where(key).with_for_update()).mappings().one()
            if row['status'] != 'needs_review' or row['reserved_day']:
                raise ValueError('Already attempted or not awaiting approval')
            app = json.loads(row['application'])
            if not app.get('requirements_verified') or not app.get('contact_verified') or not app.get('profile_verified'):
                raise ValueError('Eligibility, profile and recipient must be verified')
            if app.get('resume_digest') != hashlib.sha256((user['resume_text'] or '').encode()).hexdigest():
                raise ValueError('Résumé changed: prepare and review again')
            if bytes(user['resume'] or b'') != bytes(row['attachment']):
                raise ValueError('Original PDF changed: prepare and review again')
            if app.get('score', 0) < max(80, int(profile.get('threshold', 80))):
                raise ValueError('Match is below your application threshold')
            expected = approval_digest(app['to'], app['subject'], app['body'], row['attachment'])
            if digest != expected:
                raise ValueError('Approval does not match the current message')
            used = len(conn.execute(select(self.jobs.c.job_id).where(and_(self.jobs.c.tenant == tenant, self.jobs.c.reserved_day == day))).all())
            if used >= daily_limit:
                raise ValueError('Daily application limit reached (UTC)')
            conn.execute(update(self.jobs).where(key).values(status='sending', reserved_day=day))
        try:
            message_id = sender(gmail, app['to'], app['subject'], app['body'], row['attachment'])
        except Exception:
            # A timeout can follow successful delivery. Never automatically resend.
            with self.engine.begin() as conn:
                conn.execute(update(self.jobs).where(key).values(status='delivery_unknown'))
            raise RuntimeError('Delivery could not be confirmed. Check Gmail Sent before taking further action.') from None
        with self.engine.begin() as conn:
            conn.execute(update(self.jobs).where(key).values(status='awaiting_response', message_id=message_id))
        return message_id

    def track(self, tenant, job_id, status):
        if status not in ('saved', 'submitted', 'awaiting_response', 'interview', 'rejected', 'needs_review'):
            raise ValueError('Unknown tracking status')
        with self.engine.begin() as conn:
            key = and_(self.jobs.c.tenant == tenant, self.jobs.c.job_id == job_id)
            row = conn.execute(select(self.jobs).where(key).with_for_update()).mappings().one()
            if row['status'] in ('sending', 'delivery_unknown'):
                raise ValueError('Reconcile delivery in Gmail; this app will not retry an uncertain send')
            if row['reserved_day'] and status in ('saved', 'needs_review'):
                raise ValueError('Cannot reopen an already attempted application')
            conn.execute(update(self.jobs).where(key).values(status=status))
