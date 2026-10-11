"""Prepare private Community Cloud settings locally; never print credential values."""
from __future__ import annotations

import argparse
import base64
from getpass import getpass
import json
import os
from pathlib import Path
import re
import secrets
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

DEFAULT_APP_URL = "https://5dasesqq5hdkocoz5dupwp.streamlit.app/"
ROOT = Path(__file__).resolve().parent


def app_origin(value: str) -> str:
    try:
        parsed = urlsplit(value.strip())
        valid = (
            parsed.scheme == "https"
            and re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.streamlit\.app", parsed.hostname or "")
            and parsed.port in (None, 443)
            and not parsed.username and not parsed.password
            and parsed.path in ("", "/")
            and not parsed.query and not parsed.fragment
        )
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("Use the public HTTPS Community Cloud app address, without login parameters.")
    return "https://" + parsed.hostname + "/"


def database_url(value: str) -> str:
    """Accept provider URLs, retaining escaped credentials and enforcing verified TLS."""
    value = value.strip()
    if any(character.isspace() for character in value):
        raise ValueError("Use the provider's URL-encoded PostgreSQL connection string.")
    try:
        parsed = urlsplit(value)
        valid = (
            parsed.scheme in ("postgres", "postgresql", "postgresql+psycopg")
            and parsed.hostname not in (None, "", "localhost", "127.0.0.1", "::1")
            and parsed.username and parsed.password
            and parsed.netloc.count("@") == 1
            and parsed.path not in ("", "/")
            and not parsed.fragment
            and (parsed.port is None or 1 <= parsed.port <= 65535)
        )
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("Use a remote PostgreSQL URL with a user, password and database. URL-encode special password characters.")
    supplied_query = parse_qsl(parsed.query, keep_blank_values=True)
    certificate = dict(supplied_query).get("sslrootcert") or "system"
    query = [(key, val) for key, val in supplied_query
             if key not in ("sslmode", "sslrootcert")]
    query += [("sslmode", "verify-full"), ("sslrootcert", certificate)]
    return urlunsplit(("postgresql+psycopg", parsed.netloc, parsed.path, urlencode(query), ""))


def make_settings(app_url: str, postgres_url: str, client_id: str, client_secret: str) -> str:
    origin = app_origin(app_url)
    postgres_url = database_url(postgres_url)
    client_id = client_id.strip()
    client_secret = client_secret.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]+\.apps\.googleusercontent\.com", client_id):
        raise ValueError("Copy the Google OAuth Web application's client ID, ending in .apps.googleusercontent.com.")
    if not client_secret or client_secret.startswith("REPLACE_") or any(ord(c) < 32 for c in client_secret):
        raise ValueError("Enter the actual Google OAuth client secret, without line breaks.")
    key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")
    cookie = secrets.token_urlsafe(48)
    values = {
        "database_url": postgres_url,
        "token_encryption_key": key,
        "auth": {
            "redirect_uri": origin + "oauth2callback",
            "cookie_secret": cookie,
            "client_id": client_id,
            "client_secret": client_secret,
            "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
        },
        "gmail_oauth": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": origin,
        },
    }
    quoted = lambda val: json.dumps(val, ensure_ascii=False)
    lines = ["# PRIVATE: paste into Streamlit Secrets. Do not share or commit this file."]
    for name in ("database_url", "token_encryption_key"):
        lines.append(f"{name} = {quoted(values[name])}")
    for section in ("auth", "gmail_oauth"):
        lines += ["", f"[{section}]"]
        lines += [f"{name} = {quoted(val)}" for name, val in values[section].items()]
    return "\n".join(lines) + "\n"


def save_new_settings(path: Path, content: str) -> None:
    """Create a private file once; preserve existing tokens/keys and settings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-url", default=DEFAULT_APP_URL, help="Public Community Cloud URL; no credentials.")
    args = parser.parse_args()
    target = ROOT / ".streamlit" / "secrets.toml"
    if target.exists():
        print("A private secrets file already exists. It was not changed.", file=sys.stderr)
        print("Keep its cookie/encryption keys. Edit or copy the existing settings privately.", file=sys.stderr)
        return 2
    if not sys.stdin.isatty():
        print("Run this helper in an interactive console so private inputs can be hidden. Do not pipe credentials.", file=sys.stderr)
        return 1
    try:
        origin = app_origin(args.app_url)
        print("Create your PostgreSQL database and Google OAuth Web client first.")
        print("Register these Google redirect URLs:")
        print(origin + "oauth2callback")
        print(origin)
        print("Enter credentials here on your computer. Hidden inputs are not printed.")
        postgres = getpass("PostgreSQL connection URL (hidden): ")
        postgres = database_url(postgres)
        client_id = input("Google OAuth client ID: ")
        client_secret = getpass("Google OAuth client secret (hidden): ")
        content = make_settings(origin, postgres, client_id, client_secret)
        save_new_settings(target, content)
        print("Private settings saved to .streamlit/secrets.toml; no credential values were printed.")
        print("Paste the file contents into your Streamlit app settings -> Secrets, save and restart.")
        return 0
    except (EOFError, KeyboardInterrupt):
        print("\nSetup cancelled. No existing private settings were changed.", file=sys.stderr)
        return 130
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except FileExistsError:
        print("A private settings file appeared during setup; it was not overwritten.", file=sys.stderr)
        return 2
    except OSError:
        print("Private settings could not be saved. Check folder permissions. Credential values were not logged.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
