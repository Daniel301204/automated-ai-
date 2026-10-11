import base64
import tomllib
from urllib.parse import parse_qs, urlsplit

from cryptography.fernet import Fernet
import pytest

import configure_hosting
from configure_hosting import app_origin, database_url, make_settings, save_new_settings

APP = "https://5dasesqq5hdkocoz5dupwp.streamlit.app/"
POSTGRES = "postgres://testuser:fake%40password@example.org/demo?sslmode=require&channel_binding=require"
CLIENT = "123456-fake-client.apps.googleusercontent.com"


def test_provider_url_retains_credentials_and_enforces_verified_tls():
    parsed = urlsplit(database_url(POSTGRES))
    assert parsed.scheme == "postgresql+psycopg"
    assert parsed.netloc == "testuser:fake%40password@example.org"
    assert parse_qs(parsed.query) == {
        "sslmode": ["verify-full"], "sslrootcert": ["system"], "channel_binding": ["require"],
    }


@pytest.mark.parametrize("url", [
    "http://localhost:8502/", "https://example.org/", APP + "?code=private",
    "https://username:password@5dasesqq5hdkocoz5dupwp.streamlit.app/",
])
def test_setup_rejects_nonpublic_or_authenticated_app_links(url):
    with pytest.raises(ValueError):
        app_origin(url)


def test_generated_toml_is_valid_and_binds_both_oauth_callbacks():
    content = make_settings(APP, POSTGRES, CLIENT, 'fake-secret"with\\escaping')
    parsed = tomllib.loads(content)
    assert parsed["auth"]["redirect_uri"] == APP + "oauth2callback"
    assert parsed["gmail_oauth"]["redirect_uri"] == APP
    assert parsed["auth"]["client_id"] == parsed["gmail_oauth"]["client_id"] == CLIENT
    assert parsed["auth"]["client_secret"] == 'fake-secret"with\\escaping'
    key = parsed["token_encryption_key"]
    assert len(base64.urlsafe_b64decode(key)) == 32
    cipher = Fernet(key)
    assert cipher.decrypt(cipher.encrypt(b"test token")) == b"test token"
    assert len(parsed["auth"]["cookie_secret"]) >= 48


def test_existing_settings_and_keys_cannot_be_overwritten(tmp_path):
    path = tmp_path / ".streamlit" / "secrets.toml"
    original = make_settings(APP, POSTGRES, CLIENT, "fake-secret")
    save_new_settings(path, original)
    with pytest.raises(FileExistsError):
        save_new_settings(path, make_settings(APP, POSTGRES, CLIENT, "different-fake-secret"))
    assert path.read_text() == original


def test_connection_validation_does_not_echo_private_values():
    credential = "deliberately-private-test-value"
    with pytest.raises(ValueError) as error:
        database_url("postgres://user:" + credential + "@localhost/demo")
    assert credential not in str(error.value)


def test_provider_custom_ca_is_preserved_without_disabling_verification():
    query = parse_qs(urlsplit(database_url(POSTGRES + "&sslrootcert=%2Ftrusted%2Fca.pem")).query)
    assert query["sslmode"] == ["verify-full"]
    assert query["sslrootcert"] == ["/trusted/ca.pem"]


def test_noninteractive_console_rejected_before_private_inputs(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(configure_hosting, "ROOT", tmp_path)
    monkeypatch.setattr(configure_hosting.sys, "argv", ["configure_hosting.py"])
    monkeypatch.setattr(configure_hosting.sys.stdin, "isatty", lambda: False)
    def forbidden_prompt(*args):
        raise AssertionError("Must not prompt without an interactive console")
    monkeypatch.setattr(configure_hosting, "getpass", forbidden_prompt)
    assert configure_hosting.main() == 1
    assert "interactive console" in capsys.readouterr().err
    assert not (tmp_path / ".streamlit" / "secrets.toml").exists()


def test_cli_prepares_settings_privately_and_preserves_them_on_rerun(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(configure_hosting, "ROOT", tmp_path)
    monkeypatch.setattr(configure_hosting.sys, "argv", ["configure_hosting.py"])
    monkeypatch.setattr(configure_hosting.sys.stdin, "isatty", lambda: True)
    private_values = iter([POSTGRES, "fake-hidden-client-secret"])
    monkeypatch.setattr(configure_hosting, "getpass", lambda prompt: next(private_values))
    monkeypatch.setattr("builtins.input", lambda prompt: CLIENT)
    assert configure_hosting.main() == 0
    output = capsys.readouterr()
    assert POSTGRES not in output.out + output.err
    assert "fake-hidden-client-secret" not in output.out + output.err
    path = tmp_path / ".streamlit" / "secrets.toml"
    original = path.read_text()
    assert tomllib.loads(original)["auth"]["redirect_uri"] == APP + "oauth2callback"
    assert configure_hosting.main() == 2
    assert path.read_text() == original
