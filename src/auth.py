from __future__ import annotations

import os
from pathlib import Path

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

SCOPES: tuple[str, ...] = (
    "playlist-modify-private",
    "playlist-modify-public",
    "user-library-read",
)


def _load_env() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path if env_path.exists() else None)


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing environment variable {name}. Copy .env.example to .env and fill it in."
        )
    return value


def get_client(scopes: tuple[str, ...] = SCOPES) -> spotipy.Spotify:
    _load_env()
    auth_manager = SpotifyOAuth(
        client_id=_require("SPOTIPY_CLIENT_ID"),
        client_secret=_require("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=_require("SPOTIPY_REDIRECT_URI"),
        scope=" ".join(scopes),
        open_browser=True,
    )
    return spotipy.Spotify(auth_manager=auth_manager)
