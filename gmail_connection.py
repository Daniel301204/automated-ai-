"""Per-user Gmail OAuth with one-use state and encrypted refresh-token storage."""
import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import requests
from cryptography.fernet import Fernet
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from sqlalchemy import Table, MetaData, Column, String, Text, select, update


class GmailConnections:
    def __init__(self, engine, config, encryption_key):
        self.engine, self.config = engine, dict(config)
        self.cipher = Fernet(encryption_key.encode())
        if engine.dialect.name != 'postgresql':
            raise ValueError('Gmail connections require PostgreSQL')
        meta = MetaData()
        self.table = Table('autojob_gmail_connections', meta,
            Column('tenant', String(64), primary_key=True), Column('token', Text),
            Column('nonce_hash', String(64)), Column('expires', String(40)))
        meta.create_all(engine)

    def authorize_url(self, tenant, email):
        from sqlalchemy.dialects.postgresql import insert
        nonce = secrets.token_urlsafe(32)
        expires = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        statement = insert(self.table).values(tenant=tenant, nonce_hash=hashlib.sha256(nonce.encode()).hexdigest(), expires=expires)
        with self.engine.begin() as conn:
            conn.execute(statement.on_conflict_do_update(index_elements=['tenant'], set_={
                'nonce_hash': statement.excluded.nonce_hash, 'expires': statement.excluded.expires}))
        return 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode({
            'client_id': self.config['client_id'], 'redirect_uri': self.config['redirect_uri'],
            'response_type': 'code', 'scope': 'openid email https://www.googleapis.com/auth/gmail.send',
            'access_type': 'offline', 'prompt': 'consent', 'state': nonce, 'login_hint': email})

    def finish(self, tenant, email, state, code, session=None, verifier=id_token.verify_oauth2_token):
        if not state or not code:
            raise ValueError('Missing Gmail authorization response')
        with self.engine.begin() as conn:
            row = conn.execute(select(self.table).where(self.table.c.tenant == tenant).with_for_update()).mappings().first()
            if not row or not row['nonce_hash'] or not secrets.compare_digest(row['nonce_hash'], hashlib.sha256(state.encode()).hexdigest()):
                raise ValueError('Gmail connection state is invalid. Start the connection again.')
            if datetime.fromisoformat(row['expires']) < datetime.now(timezone.utc):
                raise ValueError('Gmail authorization expired. Start again.')
            conn.execute(update(self.table).where(self.table.c.tenant == tenant).values(nonce_hash=None, expires=None))
        session = session or requests.Session()
        result = session.post('https://oauth2.googleapis.com/token', data={
            'client_id': self.config['client_id'], 'client_secret': self.config['client_secret'],
            'redirect_uri': self.config['redirect_uri'], 'code': code, 'grant_type': 'authorization_code'}, timeout=20)
        result.raise_for_status()
        payload = result.json()
        identity = verifier(payload['id_token'], Request(session=session), self.config['client_id'])
        if not identity.get('email_verified') or identity.get('email', '').casefold() != email.casefold():
            raise ValueError('Connect the Gmail account with the same verified email as your app sign-in.')
        if 'https://www.googleapis.com/auth/gmail.send' not in payload.get('scope', '').split():
            raise ValueError('Gmail send permission was not granted; connect again and review the consent screen.')
        if not payload.get('refresh_token'):
            raise ValueError('Google did not return an offline token. Reconnect with consent.')
        encrypted = self.cipher.encrypt(json.dumps({'refresh_token': payload['refresh_token'], 'sender_email': identity['email']}).encode()).decode()
        with self.engine.begin() as conn:
            conn.execute(update(self.table).where(self.table.c.tenant == tenant).values(token=encrypted))

    def credentials(self, tenant):
        with self.engine.connect() as conn:
            token = conn.execute(select(self.table.c.token).where(self.table.c.tenant == tenant)).scalar_one_or_none()
        if not token:
            return None
        credentials = json.loads(self.cipher.decrypt(token.encode()).decode())
        return dict(client_id=self.config['client_id'], client_secret=self.config['client_secret'], **credentials)

    def disconnect(self, tenant):
        with self.engine.begin() as conn:
            conn.execute(update(self.table).where(self.table.c.tenant == tenant).values(token=None, nonce_hash=None, expires=None))
