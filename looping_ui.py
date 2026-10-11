"""LoopingCV presentation: screenshot-inspired shell and accessible native widgets."""
import html
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import quote, urlsplit
import streamlit as st
from resume_match import score

PAGES = ['Overview', 'My loops', 'Board', 'All Matches', 'Search Jobs', 'My Applications', 'Questions', 'CV Checker', 'CV Builder', 'Inbox', 'Personal Info']
ICONS = ['▦', '↻', '▤', '≡', '⌕', '▧', '?', '☑', '▤', '▣', '♙']

CSS = '''
<style>
:root { --lc-blue:#1967c3; --lc-ink:#171b24; --lc-muted:#83878c; }
html,body,[data-testid="stApp"] {font-family:'Segoe UI',Arial,sans-serif;color:var(--lc-ink)}
[data-testid="stAppViewContainer"] {background:#f7f7f9}
[data-testid="stHeader"] {display:none!important}
[data-testid="stToolbar"] {visibility:hidden}
[data-testid="stMainBlockContainer"] {max-width:none;padding:1rem 1.3rem 3rem}
[data-testid="stSidebar"] {background:#fff;border-right:1px solid #e8e8eb;min-width:274px;max-width:274px}
[data-testid="stSidebarContent"] {padding:0!important}
[data-testid="stSidebarHeader"] {display:none}
[data-testid="stSidebarUserContent"] {padding:0.8rem 0.45rem 1.5rem!important;margin:0!important;width:100%!important}
[data-testid="stElementContainer"]:has(style) {display:none}
.lc-logo {display:flex;align-items:center;gap:8px;padding:0 3px 20px;font-size:31px;font-weight:800;letter-spacing:-1.1px;color:#202020}
.lc-logo svg {width:39px;height:39px;flex-shrink:0}
[data-testid="stSidebar"] [data-testid="stRadio"] label {padding:13px 10px;border-radius:5px;min-height:49px}
[data-testid="stSidebar"] [data-testid="stRadioOption"]>div>div:first-child {display:none}
[data-testid="stSidebar"] [data-testid="stRadio"] label p {font-size:16px!important;font-weight:400;white-space:nowrap}
[data-testid="stSidebar"] [data-testid="stRadio"] label p:first-letter {color:#858585}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {background:#e5e5e5;color:#111827}
[data-testid="stSidebar"] [data-testid="stRadio"]>div {gap:2px}
[data-testid="stSidebar"] [data-testid="stRadioOption"] {width:100%;padding:11px 10px;border-radius:5px;min-height:46px;box-sizing:border-box}
[data-testid="stSidebar"] [data-testid="stRadioOption"] p {font-size:16px!important;font-weight:400;white-space:nowrap}
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] {background:#e5e5e5;color:#111827}
[data-testid="stSidebar"] [role="radiogroup"] {gap:2px;align-items:stretch}
[data-testid="stSidebar"] [data-testid="stRadio"],[data-testid="stSidebar"] [data-testid="stRadioGroup"],[data-testid="stSidebar"] [data-testid="stRadioGroup"]>div {width:100%!important}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stRadioOption"] {width:100%!important;padding:11px 10px;min-height:46px}
[data-testid="stSidebar"] button[kind] {border-radius:28px;min-height:48px;width:100%;border-color:var(--lc-blue);color:var(--lc-blue);font-size:16px}
[data-testid="stSidebar"] button[kind="primary"] {background:var(--lc-blue);color:#fff;box-shadow:0 2px 3px #0002}
.st-key-sidebar_footer {border-top:1px solid #f0f0f0;padding-top:18px;margin-top:24px;max-width:225px}
.st-key-topbar {background:#fff;margin:-1rem -1.3rem 0;padding:9px 18px;border-bottom:1px solid #f1f1f3;min-height:64px}
.st-key-topbar [data-testid="stVerticalBlock"] {gap:0}
.st-key-topbar button {border:0;background:#fff;box-shadow:none;min-height:42px;white-space:nowrap}
.st-key-topbar button[kind="primary"] {background:var(--lc-blue);color:#fff;border-radius:25px;padding:0 22px;box-shadow:0 2px 3px #0002}
.lc-page-title {font-size:23px!important;font-weight:400!important;line-height:42px;margin:0}
.lc-intro {padding:16px 0 26px}
.lc-intro h1 {font-size:28px!important;font-weight:400!important;letter-spacing:-.7px;margin:0 0 11px!important;padding:0!important;line-height:1.3!important}
.lc-intro p {font-size:20px!important;font-weight:400;margin:0!important}
.st-key-loop_content {padding-left:clamp(0px,9vw,148px);padding-top:4px}
.lc-stepper {display:flex;align-items:center;width:100%;margin:12px 0 30px;padding:0 24px}
.lc-step {display:flex;align-items:center;gap:9px;color:#8b8b8b;font-size:18px;white-space:nowrap}
.lc-step .number {display:grid;place-items:center;border-radius:50%;width:27px;height:27px;background:#b9b9b9;color:#fff;font-size:14px}
.lc-step.active {color:#151b25}.lc-step.active .number,.lc-step.done .number {background:#1967c3}
.lc-connector {height:1px;background:#e6e6e8;flex:1;margin:0 12px;min-width:15px}
.st-key-wizard_card,.st-key-personal_card,.st-key-content_card {background:white;padding:27px 30px;border:1px solid #f4f4f5;border-radius:5px}
.st-key-wizard_card h3 {font-size:19px!important;font-weight:400!important;margin:0 0 16px!important;padding:0!important}
.st-key-wizard_card [data-testid="stForm"] [data-testid="stVerticalBlock"] {gap:10px!important}
h1 {font-size:28px!important;font-weight:500!important}h2 {font-size:23px!important;font-weight:500!important}h3 {font-size:19px!important}
[data-testid="stTextInput"] input,[data-testid="stSelectbox"] [data-baseweb="select"]>div,[data-testid="stMultiSelect"] [data-baseweb="select"]>div {background:#fff;border:1px solid #aaa;border-radius:4px;min-height:56px;font-size:17px}
[data-testid="stTextInputRootElement"] {background:#fff!important;border:1px solid #aaa!important;border-radius:4px!important;min-height:60px!important}
[data-testid="stTextInputField"] {background:#fff!important;border:0!important;min-height:58px!important;font-size:17px!important}
[data-testid="stSelectbox"] .react-aria-ComboBox>[role="group"],[data-testid="stMultiSelect"]>div[role="group"],[data-testid="stMultiSelect"]>div>div[role="group"] {background:#fff!important;border:1px solid #aaa!important;border-radius:4px!important;min-height:60px!important;padding:0 12px!important}
[data-testid="stSelectbox"] [role="combobox"] {min-height:58px!important;font-size:17px!important}
[data-testid="stSelectbox"] button {background:#fff!important;min-height:58px!important;border:0!important}
[data-testid="stTextArea"] textarea {background:#fff;border:1px solid #aaa;border-radius:4px;font-size:16px}
[data-testid="stTextInput"] label,[data-testid="stSelectbox"] label,[data-testid="stMultiSelect"] label,[data-testid="stTextArea"] label {color:#858585;font-size:13px}
[data-testid="stForm"] {border:0;padding:0}
[data-testid="stCheckbox"] label p {font-size:17px;color:#777}
.st-key-wizard_card [data-testid="stCheckbox"] {margin:11px 0}
[data-testid="stCaptionContainer"] p {color:#8b8b8b;font-size:13px}
button[kind="primary"],button[kind="primaryFormSubmit"] {background:#1967c3;border-color:#1967c3;border-radius:5px;min-height:42px}
button[kind="secondary"],button[kind="secondaryFormSubmit"] {background:#fff;border-radius:5px;min-height:42px}
[data-testid="stTabs"] [data-baseweb="tab-list"] {gap:26px;border-bottom:1px solid #eee}
[data-testid="stTabs"] button {padding:12px 15px;letter-spacing:1px;font-size:16px}
[data-testid="stTabs"] button p {font-size:16px!important;letter-spacing:1px!important}
.st-key-topbar button p,[data-testid="stSidebar"] button p {font-size:16px!important}
[data-testid="stTabs"] [aria-selected="true"] {color:#1967c3}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {background:#1967c3}
[data-testid="stTabs"] [data-testid="stTab"] {padding:12px 15px;letter-spacing:1px}
[data-testid="stTabs"] [data-testid="stTab"] p {font-size:16px!important;letter-spacing:1px}
[data-testid="stTabs"] [role="tablist"] {gap:4px}
[data-testid="stTabs"] .react-aria-SelectionIndicator {background:#1967c3}
.st-key-personal_form {max-width:980px;padding:24px 30px}
.st-key-personal_form [data-testid="stTextInput"] {margin-bottom:26px}
.st-key-personal_form [data-testid="stTextInput"],.st-key-wizard_card [data-testid="stTextInput"] {position:relative;margin-top:8px}
.st-key-personal_form [data-testid="stTextInput"]>label,.st-key-wizard_card [data-testid="stTextInput"]>label {position:absolute;top:-8px;left:14px;z-index:1;background:#fff;padding:0 4px;min-height:0;width:auto}
.st-key-personal_form [data-testid="stTextInput"]>label p,.st-key-wizard_card [data-testid="stTextInput"]>label p {font-size:13px!important;color:#83878c}
.lc-empty {padding:44px 20px;text-align:center;background:#fff;border:1px solid #eee;border-radius:6px;margin:12px 0 24px}
.lc-empty strong {display:block;font-size:21px;font-weight:500;margin-bottom:10px}
.lc-empty p {margin:0;color:#83878c;font-size:15px}
.lc-badge {display:inline-block;padding:4px 11px;color:#1967c3;background:#eef5ff;border-radius:18px;font-size:12px;margin-bottom:12px}
[data-testid="stMetric"] {background:white;padding:23px;border:1px solid #eee;border-radius:6px}
[data-testid="stExpander"] {background:#fff;border-color:#e9e9ee}
.lc-page-description {color:#8d949e;font-size:15px;margin:0 0 24px;line-height:1.6}
.lc-overview-greeting {font-size:28px!important;font-weight:600!important;margin:14px 0 2px!important;padding:0!important}
.lc-summary-grid {display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:24px;margin:12px 0 22px}
.lc-summary-card {background:#fff;min-height:140px;border-radius:16px;border:1px solid #eeeff2;box-shadow:0 9px 20px #24324b05;position:relative;padding:22px}
.lc-summary-label {font-size:15px;font-weight:400;margin:0 42px 12px 0;line-height:1.35}
.lc-summary-value {font-size:32px;font-weight:600;line-height:1.1}
.lc-summary-icon {position:absolute;right:20px;top:20px;border-radius:13px;width:44px;height:44px;display:grid;place-items:center}
.lc-blue {color:#1967c3;background:#eff5ff}.lc-violet {color:#6650ee;background:#f3f0ff}.lc-green {color:#059669;background:#eafbf3}.lc-orange {color:#e48b00;background:#fff9e9}.lc-red {color:#e52351;background:#fff1f4}
.lc-summary-icon svg,.lc-setup-icon svg {width:23px;height:23px}
.st-key-setup_panel {background:#fff;padding:12px 14px;border-radius:7px;max-width:330px;margin-top:8px}
.st-key-setup_panel [data-testid="stVerticalBlock"] {gap:10px}
.st-key-setup_profile,.st-key-setup_answers,.st-key-setup_loop,.st-key-setup_cv {border:1px solid #d7d8da;border-radius:5px;padding:10px;min-height:70px}
.st-key-setup_panel [data-testid="stHorizontalBlock"] {align-items:center!important;gap:10px!important;flex-wrap:nowrap!important}
.st-key-setup_panel [data-testid="stColumn"] {min-width:0!important}
.st-key-setup_panel [data-testid="stColumn"]:first-child {flex:0 0 44px!important;width:44px!important}
.st-key-setup_panel [data-testid="stColumn"]:nth-child(2) {flex:1 1 auto!important}
.st-key-setup_panel [data-testid="stColumn"]:last-child {flex:0 0 40px!important;width:40px!important}
.st-key-setup_panel p {font-size:17px;margin:0}
.st-key-setup_panel button {border:0;background:transparent;color:#1967c3;min-height:36px;padding:0 4px}
.lc-setup-icon {width:44px;height:44px;display:grid;place-items:center;background:#e8f4ff;color:#1967c3;border-radius:50%}
.lc-status {font-size:12px;padding:5px 10px;border-radius:20px;display:inline-block;white-space:nowrap;color:#526074;background:#f1f4f8}
.lc-status.active,.lc-status.awaiting_response,.lc-status.interview {color:#087957;background:#eafbf3}
.lc-status.needs_review,.lc-status.delivery_unknown {color:#a66b00;background:#fff7e5}
.lc-status.rejected {color:#c22f50;background:#fff0f3}
.lc-job-heading {display:flex;gap:14px;align-items:flex-start;margin:0 0 12px}
.lc-company-icon {flex:0 0 42px;height:42px;border-radius:10px;background:#eef5ff;color:#1967c3;display:grid;place-items:center;font-size:17px;font-weight:600}
.lc-job-heading h3 {margin:0!important;padding:0!important;font-weight:500!important;font-size:18px!important}
.lc-job-meta {font-size:13px;color:#83878c;margin-top:5px;line-height:1.5}
.lc-job-content {flex:1;min-width:0;overflow-wrap:anywhere}
.lc-chips {display:flex;gap:7px;flex-wrap:wrap;margin:8px 0 16px}
.lc-chip {padding:5px 10px;background:#f0f6fd;border:1px solid #e4edf8;border-radius:5px;color:#2462a2;font-size:13px}
[data-testid="stVerticalBlockBorderWrapper"]>div {border-color:#e8eaee!important;border-radius:9px!important;background:#fff}
.st-key-board_columns {margin-top:8px}
.lc-board-label {display:flex;justify-content:space-between;align-items:center;font-size:14px;font-weight:600;margin:0 0 14px;border-bottom:2px solid #dbe7fa;padding-bottom:12px}
.lc-board-count {color:#7e8896;background:#edf0f5;border-radius:6px;padding:2px 7px;font-size:12px}
.st-key-personal_card {margin-top:18px}
.st-key-search_controls,.st-key-cv_upload {background:#fff;padding:24px;border:1px solid #eee;border-radius:7px;margin-top:10px}
.st-key-search_controls [data-testid="stHorizontalBlock"] {align-items:flex-end}
.st-key-cv_upload [data-testid="stFileUploader"] {margin-bottom:8px}
.st-key-topbar [data-testid="stColumn"]:last-child button p {font-size:14px!important;letter-spacing:.3px;max-width:180px;overflow:hidden;text-overflow:ellipsis}
@media(max-width:1450px) {.lc-summary-grid{gap:16px}.lc-summary-card{padding:18px}.lc-summary-icon{right:14px;width:36px;height:36px}.lc-summary-label{font-size:13px;margin-right:34px}}
@media(max-width:1150px) {.lc-summary-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.st-key-topbar [data-testid="stColumn"]:nth-child(3){display:none}}
@media(max-width:900px) {.st-key-loop_content {padding-left:0}.lc-stepper {padding:0}.lc-step {font-size:13px;gap:5px}.lc-connector {margin:0 7px}.st-key-wizard_card,.st-key-personal_card {padding:20px 16px}.st-key-personal_form {padding:20px 4px}.lc-intro {padding-bottom:20px}}
@media(max-width:550px) {[data-testid="stMainBlockContainer"] {padding:1rem 0.7rem}.st-key-topbar {margin:-1rem -.7rem 0;padding:8px}.lc-step {font-size:11px}.lc-step .number {width:23px;height:23px}.lc-intro h1 {font-size:23px}.lc-intro p {font-size:17px}}
@media(max-width:550px) {
.st-key-topbar [data-testid="stHorizontalBlock"] {flex-wrap:nowrap!important;gap:6px!important}
.st-key-topbar [data-testid="stColumn"] {flex:0 0 auto!important;min-width:0!important;width:auto!important}
.st-key-topbar [data-testid="stColumn"]:nth-child(1) {width:28px!important}
.st-key-topbar [data-testid="stColumn"]:nth-child(2) {flex:1 1 auto!important}
.st-key-topbar [data-testid="stColumn"]:nth-child(3) {display:none}
.st-key-topbar [data-testid="stColumn"]:nth-child(4) {width:96px!important}
.st-key-topbar [data-testid="stColumn"]:nth-child(5) {width:25px!important}
.st-key-topbar button[kind="primary"] {padding:0 12px}
.lc-page-title {font-size:18px!important;white-space:nowrap}
.lc-intro h1 {font-size:23px!important}.lc-intro p {font-size:17px!important}
.lc-step {gap:4px;flex:0 1 auto}.lc-step span:last-child {white-space:normal;max-width:54px;line-height:14px}
.lc-connector {min-width:4px;margin:0 3px}
.lc-summary-grid {grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.lc-summary-card {min-height:125px;padding:16px}.lc-summary-value {font-size:28px}.lc-summary-label {font-size:12px;margin-right:30px}
.lc-summary-icon {right:12px;top:16px;width:30px;height:30px;border-radius:9px}.lc-summary-icon svg {width:19px;height:19px}
.st-key-topbar [data-testid="stColumn"]:last-child button p {font-size:0!important}.st-key-topbar [data-testid="stColumn"]:last-child button p:first-letter {font-size:18px!important}
.st-key-search_controls,.st-key-cv_upload {padding:16px}
.lc-job-heading {gap:10px}.lc-company-icon {flex-basis:34px;height:34px}
.lc-overview-greeting {font-size:24px!important}
}
</style>
'''


def go(page):
    st.session_state.active_page = page
    st.session_state.sidebar_hidden = False


def theme():
    st.markdown(CSS, unsafe_allow_html=True)
    if st.session_state.get('sidebar_hidden'):
        st.markdown('<style>@media(min-width:769px){[data-testid="stSidebar"]{display:none}}@media(max-width:768px){[data-testid="stSidebar"]{display:block!important;visibility:visible!important;transform:translateX(0)!important;left:0!important;position:fixed!important;z-index:1001}}</style>', unsafe_allow_html=True)
    else:
        st.markdown('<style>@media(max-width:768px){[data-testid="stSidebar"]{display:none!important}}</style>', unsafe_allow_html=True)


def logo():
    st.markdown('''<div class="lc-logo"><svg viewBox="0 0 48 48" aria-hidden="true"><path d="M8 22A16 16 0 0 1 35 12" fill="none" stroke="#202020" stroke-width="5"/><path d="M35 5v13H22" fill="#202020"/><path d="M40 27A16 16 0 0 1 13 37" fill="none" stroke="#202020" stroke-width="5"/><path d="M13 44V31h13" fill="#202020"/></svg><span>loopingcv</span></div>''', unsafe_allow_html=True)


def public_share_url(redirect_uri):
    """Return only the public Community Cloud origin, without OAuth data."""
    if not isinstance(redirect_uri, str):
        return None
    try:
        parsed = urlsplit(redirect_uri.strip())
        host = parsed.hostname or ''
        if (parsed.scheme != 'https' or parsed.username or parsed.password
                or parsed.port not in (None, 443)
                or not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.streamlit\.app', host)):
            return None
        return 'https://' + host + '/'
    except ValueError:
        return None


def sidebar(public_url=None):
    with st.sidebar:
        if st.session_state.get('sidebar_hidden'):
            st.button('Close navigation', on_click=lambda: st.session_state.update(sidebar_hidden=False))
        logo()
        current = st.session_state.get('active_page', 'Overview')
        selected = current if current in PAGES else None
        if st.session_state.get('sidebar_nav') != selected:
            st.session_state.sidebar_nav = selected
        st.radio('Navigation', PAGES, key='sidebar_nav', index=None, width='stretch', label_visibility='collapsed',
                 format_func=lambda p: ICONS[PAGES.index(p)] + '  ' + p,
                 on_change=lambda: go(st.session_state.sidebar_nav))
        with st.container(key='sidebar_footer'):
            st.button('＋ New Loop', type='primary', on_click=go, args=('New Loop',), key='sidebar_new', use_container_width=True)
            st.button('ⓘ Help - FAQ', on_click=go, args=('Questions',), use_container_width=True)
            st.button('♙ Personal Info', on_click=go, args=('Personal Info',), use_container_width=True)
            with st.popover('Share app', use_container_width=True):
                if public_url:
                    st.caption('Your friends sign in to their own private workspace.')
                    st.code(public_url, language=None)
                    message = 'Try LoopingCV for job search and application review: ' + public_url
                    st.link_button('Share on WhatsApp', 'https://wa.me/?text=' + quote(message, safe=''))
                else:
                    st.info('Publish LoopingCV on Streamlit Community Cloud to get a link your friends can open. Configure the public Google sign-in redirect in Streamlit Secrets. A localhost address is only available on your computer.')
                    st.link_button('Open Streamlit Community Cloud', 'https://share.streamlit.io/')
            st.caption('English · Your job workspace')


def header(page, local, name=''):
    with st.container(key='topbar'):
        menu, title, changelog, new, account = st.columns([.35, 6.5, 1.2, 1.05, 1.35], vertical_alignment='center')
        with menu:
            st.button('☰', help='Show or hide navigation', key='menu_toggle', on_click=lambda: st.session_state.update(sidebar_hidden=not st.session_state.get('sidebar_hidden', False)))
        with title:
            st.markdown('<p class="lc-page-title">' + html.escape(page) + '</p>', unsafe_allow_html=True)
        with changelog:
            with st.popover('Changelog'):
                st.write('LoopingCV update')
                st.write('Screenshot-inspired navigation, personal profile and a four-step loop builder. Approval is required before every email.')
        with new:
            st.button('New Loop', type='primary', key='header_new', on_click=go, args=('New Loop',))
        with account:
            st.button('♙ ' + (name or 'My profile'), help='Personal info', key='header_account', on_click=go, args=('Personal Info',))


def icon(name):
    paths = {
        'loop': '<path d="M20 8a8 8 0 1 0 1 8M20 3v5h-5"/>',
        'person': '<circle cx="12" cy="8" r="4"/><path d="M4 22v-3a8 8 0 0 1 16 0v3"/>',
        'questions': '<path d="M9 8a3 3 0 0 1 6 0c0 3-3 2-3 5M12 17h.01"/><rect x="3" y="2" width="18" height="20" rx="5"/>',
        'document': '<path d="M6 2h8l4 4v16H6zM14 2v5h4M9 12h6M9 16h6"/>',
        'matches': '<circle cx="6" cy="12" r="2"/><circle cx="18" cy="5" r="2"/><circle cx="18" cy="19" r="2"/><path d="m8 11 8-5M8 13l8 5"/>',
        'email': '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
        'pending': '<circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 17h.01"/>',
    }
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + paths.get(name, paths['document']) + '</svg>'


def description(text):
    st.markdown('<p class="lc-page-description">' + html.escape(text) + '</p>', unsafe_allow_html=True)


def status_badge(status):
    state = status if status in ('active', 'paused', 'discovered', 'saved', 'needs_review', 'submitted', 'awaiting_response', 'interview', 'rejected', 'sending', 'delivery_unknown') else 'needs_review'
    st.markdown('<span class="lc-status ' + state + '">' + html.escape(state.replace('_', ' ').title()) + '</span>', unsafe_allow_html=True)


def job_heading(job):
    company = str(job.get('company') or 'Employer')
    location = str(job.get('location') or 'Location not provided')
    st.markdown('<div class="lc-job-heading"><span class="lc-company-icon">' + html.escape(company[:2].upper()) + '</span><div class="lc-job-content"><h3>' + html.escape(str(job.get('title') or 'Untitled role')) + '</h3><div class="lc-job-meta">' + html.escape(company + ' · ' + location) + '</div></div></div>', unsafe_allow_html=True)


def skill_chips(skills):
    st.markdown('<div class="lc-chips">' + ''.join('<span class="lc-chip">' + html.escape(str(skill)) + '</span>' for skill in skills) + '</div>', unsafe_allow_html=True)


def dashboard_counts(rows, loops, resume, threshold):
    """Derive displayed activity from real records; uncertain sends never count as sent."""
    submitted = ('submitted', 'awaiting_response', 'interview', 'rejected')
    matches = sum(score(resume or '', json.loads(row['payload']))['match_score'] >= max(int(threshold), int(json.loads(row['payload']).get('loop_threshold', 80))) for row in rows)
    return [
        ('Active Loops', sum(bool(row['enabled']) for row in loops), 'loop', 'blue'),
        ('Total Matches', matches, 'matches', 'violet'),
        ('Applications Submitted', sum(bool(row.get('message_id')) or row['status'] in submitted for row in rows), 'document', 'green'),
        ('Emails Sent', sum(bool(row.get('message_id')) for row in rows), 'email', 'orange'),
        ('Pending applications', sum(row['status'] in ('needs_review', 'sending', 'delivery_unknown') for row in rows), 'pending', 'red'),
    ]


def overview_cards(items):
    cards = []
    for label, value, symbol, color in items:
        cards.append('<div class="lc-summary-card"><div class="lc-summary-label">' + html.escape(label) + '</div><div class="lc-summary-value">' + str(int(value)) + '</div><div class="lc-summary-icon lc-' + color + '">' + icon(symbol) + '</div></div>')
    st.markdown('<div class="lc-summary-grid">' + ''.join(cards) + '</div>', unsafe_allow_html=True)


def setup_item(label, symbol, complete, page, key):
    with st.container(key='setup_' + key):
        image, text, action = st.columns([.7, 3.5, .6], vertical_alignment='center')
        image.markdown('<span class="lc-setup-icon">' + icon(symbol) + '</span>', unsafe_allow_html=True)
        text.write(label)
        action.button('✓' if complete else 'Go', help=('Completed · edit' if complete else label), on_click=go, args=(page,), key='setup_action_' + key)


def greeting(name):
    today = datetime.now(ZoneInfo('Asia/Kolkata'))
    st.markdown('<h1 class="lc-overview-greeting">Hello, ' + html.escape(name or 'there') + '</h1>', unsafe_allow_html=True)
    description("Here’s what’s happening with your job search today, " + today.strftime('%A, %B ') + str(today.day) + '.')


def empty(title, text):
    st.markdown('<div class="lc-empty"><strong>' + html.escape(title) + '</strong><p>' + html.escape(text) + '</p></div>', unsafe_allow_html=True)


def stepper(step):
    labels = ['Search Info', 'Email Template', 'Settings', 'Review']
    pieces = ['<div class="lc-stepper" aria-label="Loop setup progress">']
    for index, label in enumerate(labels):
        state = 'active' if index == step else ('done' if index < step else '')
        pieces.append(f'<div class="lc-step {state}"><span class="number">{index+1}</span><span>{label}</span></div>')
        if index < 3:
            pieces.append('<span class="lc-connector"></span>')
    st.markdown(''.join(pieces) + '</div>', unsafe_allow_html=True)
