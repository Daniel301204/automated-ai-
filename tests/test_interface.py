import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from looping_ui import dashboard_counts
from workflow import Store


def test_dashboard_does_not_count_uncertain_or_manual_sends_as_gmail_delivery():
    job = dict(title='Python Developer', description='Python SQL', loop_threshold=80)
    def row(status, message_id=None):
        return dict(status=status, message_id=message_id, payload=json.dumps(job))
    rows = [row('submitted'), row('delivery_unknown'), row('sending'),
            row('needs_review'), row('awaiting_response', 'confirmed-gmail-id')]
    counts = {label: value for label, value, _, _ in dashboard_counts(
        rows, [{'enabled': True}, {'enabled': False}], 'Python developer SQL', 80)}
    assert counts['Active Loops'] == 1
    assert counts['Applications Submitted'] == 2
    assert counts['Emails Sent'] == 1
    assert counts['Pending applications'] == 3


def test_dashboard_matches_use_current_resume_and_loop_threshold():
    rows = [dict(status='discovered', message_id=None, payload=json.dumps({
        'title': 'Python Developer', 'description': 'Python SQL',
        'match_score': 100, 'loop_threshold': 90,
    }))]
    before = {label: value for label, value, _, _ in dashboard_counts(rows, [], 'Python developer SQL', 80)}
    after = {label: value for label, value, _, _ in dashboard_counts(rows, [], 'React JavaScript', 80)}
    assert before['Total Matches'] == 1
    assert after['Total Matches'] == 0


def test_checklist_navigation_and_profile_save_keep_sidebar_in_sync(monkeypatch, tmp_path):
    url = 'sqlite:///' + str(tmp_path / 'navigation.db')
    monkeypatch.setenv('AUTOJOB_LOCAL_DEV', '1')
    monkeypatch.setenv('AUTOJOB_DATABASE_URL', url)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'streamlit_app.py'), default_timeout=20).run()
    assert not app.exception
    assert app.sidebar.radio[0].value == 'Overview'
    app.button(key='setup_action_profile').click().run()
    assert app.sidebar.radio[0].value == 'Personal Info'
    next(field for field in app.text_input if field.label == 'First Name').set_value('Example')
    next(field for field in app.text_input if field.label == 'Last Name').set_value('Candidate')
    next(button for button in app.button if button.label == 'Save personal info').click().run()
    assert not app.exception
    assert json.loads(Store(url).profile('local-development')['profile'])['name'] == 'Example Candidate'
    app.button(key='header_new').click().run()
    assert app.session_state.active_page == 'New Loop'
    assert app.sidebar.radio[0].value is None
    app.sidebar.radio[0].set_value('Overview').run()
    assert not app.exception
    assert app.sidebar.radio[0].value == 'Overview'
    assert any('Hello, Example' in block.value for block in app.markdown)
    app.button(key='setup_action_answers').click().run()
    assert app.sidebar.radio[0].value == 'Questions'
    app.text_area(key='questions_answers').set_value('Example answer checked against original documents.')
    app.button(key='questions_save').click().run()
    assert not app.exception
    assert json.loads(Store(url).profile('local-development')['profile'])['answers'] == 'Example answer checked against original documents.'
