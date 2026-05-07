"""Autenticação com a API do Spotify via OAuth."""

import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

SCOPES = [
    "playlist-modify-private",
    "playlist-modify-public",
    "playlist-read-private",
    "playlist-read-collaborative",
    "user-library-read",
]


def get_client() -> spotipy.Spotify:
    """Cria e devolve um cliente Spotify autenticado via OAuth.

    Lê as credenciais das variáveis de ambiente e guarda o token
    de acesso em ficheiro .cache para reutilização.

    Returns:
        Cliente Spotify autenticado e pronto a usar.

    Raises:
        spotipy.SpotifyException: Se a autenticação falhar.
    """
    auth_manager = SpotifyOAuth(
        client_id=os.environ["SPOTIPY_CLIENT_ID"],
        client_secret=os.environ["SPOTIPY_CLIENT_SECRET"],
        redirect_uri=os.environ["SPOTIPY_REDIRECT_URI"],
        scope=" ".join(SCOPES),
        cache_path=".cache",
        open_browser=True,
    )
    return spotipy.Spotify(auth_manager=auth_manager)
