"""LoopingCV presentation: screenshot-inspired shell and accessible native widgets."""
import html
import re
from urllib.parse import quote, urlsplit
import streamlit as st

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
[data-testid="stSidebar"] {background:#fff;border-right:1px solid #e8e8eb;min-width:270px;max-width:270px}
[data-testid="stSidebarContent"] {padding:0!important}
[data-testid="stSidebarHeader"] {display:none}
[data-testid="stSidebarUserContent"] {padding:0.8rem 0.7rem 1.5rem!important;margin:0!important;width:100%!important}
[data-testid="stElementContainer"]:has(style) {display:none}
.lc-logo {display:flex;align-items:center;gap:8px;padding:0 3px 20px;font-size:31px;font-weight:800;letter-spacing:-1.1px;color:#202020}
.lc-logo svg {width:39px;height:39px;flex-shrink:0}
[data-testid="stSidebar"] [data-testid="stRadio"] label {padding:11px 8px;border-radius:5px;min-height:44px}
[data-testid="stSidebar"] [data-testid="stRadioOption"]>div>div:first-child {display:none}
[data-testid="stSidebar"] [data-testid="stRadio"] label p {font-size:16px!important;font-weight:400;white-space:nowrap}
[data-testid="stSidebar"] [data-testid="stRadio"] label p:first-letter {color:#858585}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {background:#f0f6fd;color:var(--lc-blue)}
[data-testid="stSidebar"] [data-testid="stRadio"]>div {gap:2px}
[data-testid="stSidebar"] button[kind] {border-radius:28px;min-height:48px;width:100%;border-color:var(--lc-blue);color:var(--lc-blue);font-size:16px}
[data-testid="stSidebar"] button[kind="primary"] {background:var(--lc-blue);color:#fff;box-shadow:0 2px 3px #0002}
.st-key-sidebar_footer {border-top:1px solid #f0f0f0;padding-top:18px;margin-top:22px}
.st-key-topbar {background:#fff;margin:-1rem -1.3rem 0;padding:9px 22px;border-bottom:1px solid #f1f1f3}
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
.st-key-wizard_card,.st-key-personal_card,.st-key-content_card {background:white;padding:27px 30px;border:1px solid #f4f4f5;border-radius:0}
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
.st-key-personal_form {max-width:980px;padding:24px 30px}
.st-key-personal_form [data-testid="stTextInput"] {margin-bottom:26px}
.lc-empty {padding:44px 20px;text-align:center;background:#fff;border:1px solid #eee;border-radius:6px;margin:12px 0 24px}
.lc-empty strong {display:block;font-size:21px;font-weight:500;margin-bottom:10px}
.lc-empty p {margin:0;color:#83878c;font-size:15px}
.lc-badge {display:inline-block;padding:4px 11px;color:#1967c3;background:#eef5ff;border-radius:18px;font-size:12px;margin-bottom:12px}
[data-testid="stMetric"] {background:white;padding:23px;border:1px solid #eee;border-radius:6px}
[data-testid="stExpander"] {background:#fff;border-color:#e9e9ee}
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
        st.radio('Navigation', PAGES, key='sidebar_nav', label_visibility='collapsed',
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
            st.caption('English · Private workspace')


def header(page, local):
    with st.container(key='topbar'):
        menu, title, changelog, new, account = st.columns([.35, 5.5, 1.2, 1.05, .45], vertical_alignment='center')
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
            st.button('♙', help='Personal info', key='header_account', on_click=go, args=('Personal Info',))


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
