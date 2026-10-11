from pathlib import Path
from types import SimpleNamespace

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from resume_match import score
import workflow


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('settings', [
    {}, {'database_url': 'postgresql+psycopg://unavailable/demo'},
    {'auth': {'client_id': 'partial-owner-settings'}},
])
def test_incomplete_hosting_shows_demo_without_private_storage_or_send(monkeypatch, settings):
    monkeypatch.delenv('AUTOJOB_LOCAL_DEV', raising=False)
    def forbidden(*args, **kwargs):
        raise AssertionError('Public demo must not access private storage or send mail')
    monkeypatch.setattr(workflow, 'Store', forbidden)
    monkeypatch.setattr(workflow, 'send_gmail', forbidden)
    app = AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=15)
    app.secrets.update(settings)
    app.run()
    assert not app.exception
    assert 'LoopingCV' in app.title[0].value
    assert 'Public demo' in app.info[0].value
    assert len(app.get('file_uploader')) == 0
    assert next(button for button in app.button if 'Approve and send' in button.label).disabled
    assert next(metric for metric in app.metric if metric.label == 'Applications sent').value == '0'


def test_demo_uses_real_matcher_and_role_selector_updates_results(monkeypatch):
    monkeypatch.delenv('AUTOJOB_LOCAL_DEV', raising=False)
    app = AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=15).run()
    assert not app.exception
    initial = next(metric for metric in app.metric if metric.label == 'Text similarity').value
    app.selectbox(key='public_demo_role').set_value('Frontend Developer').run()
    assert not app.exception
    resume = (ROOT / 'docs/capstone/demo_resume.txt').read_text()
    expected = score(resume, {
        'title': 'Frontend Developer',
        'description': 'Frontend developer using JavaScript, React and TypeScript.',
    })['match_score']
    updated = next(metric for metric in app.metric if metric.label == 'Text similarity').value
    assert updated == str(expected) + '%'
    assert updated != initial
    assert next(button for button in app.button if 'Approve and send' in button.label).disabled


def test_configured_private_workspace_still_requires_sign_in(monkeypatch):
    monkeypatch.delenv('AUTOJOB_LOCAL_DEV', raising=False)
    # AppTest has no browser authentication handler to populate st.user.
    monkeypatch.setattr(st, 'user', SimpleNamespace(is_logged_in=False))
    app = AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=15)
    app.secrets.update({
        'database_url': 'postgresql+psycopg://unavailable/demo',
        'auth': {'redirect_uri': 'https://example.streamlit.app/oauth2callback',
                 'cookie_secret': 'fictional-test-cookie', 'client_id': 'fictional-test-client',
                 'client_secret': 'fictional-test-secret',
                 'server_metadata_url': 'https://accounts.google.com/.well-known/openid-configuration'},
    })
    app.run()
    assert not app.exception
    assert app.title[0].value == 'Sign in to your private job workspace'
    assert any(button.label == 'Sign in' for button in app.button)
    assert len(app.get('file_uploader')) == 0
    assert not any('Public demo' in item.value for item in app.info)
