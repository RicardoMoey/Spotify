"""Operações sobre playlists do Spotify."""

from dataclasses import dataclass
from typing import Optional
import spotipy

CHUNK_SIZE = 100


@dataclass
class Playlist:
    """Representa uma playlist do Spotify."""

    id: str
    name: str
    owner: str
    public: bool
    track_count: int
    uri: str


def list_user_playlists(client: spotipy.Spotify) -> list[Playlist]:
    """Lista todas as playlists do utilizador autenticado, com paginação.

    Args:
        client: Cliente Spotify autenticado.

    Returns:
        Lista de Playlist com todas as playlists do utilizador.
    """
    playlists: list[Playlist] = []
    limit = 50
    offset = 0

    while True:
        response = client.current_user_playlists(limit=limit, offset=offset)
        items = response.get("items") or []

        for item in items:
            playlists.append(
                Playlist(
                    id=item["id"],
                    name=item["name"],
                    owner=item["owner"]["display_name"] or item["owner"]["id"],
                    public=item.get("public") or False,
                    track_count=(item.get("items") or item.get("tracks") or {}).get("total", 0),
                    uri=item["uri"],
                )
            )

        if response.get("next") is None:
            break
        offset += limit

    return playlists


def find_playlist_by_name(
    client: spotipy.Spotify, name: str
) -> Optional[Playlist]:
    """Procura uma playlist pelo nome exacto (sensível a maiúsculas).

    Args:
        client: Cliente Spotify autenticado.
        name: Nome da playlist a procurar.

    Returns:
        Playlist encontrada ou None se não existir.
    """
    for playlist in list_user_playlists(client):
        if playlist.name == name:
            return playlist
    return None


def create_playlist(
    client: spotipy.Spotify,
    name: str,
    description: str = "",
    public: bool = False,
) -> Playlist:
    """Cria uma nova playlist para o utilizador autenticado.

    Args:
        client: Cliente Spotify autenticado.
        name: Nome da nova playlist.
        description: Descrição opcional da playlist.
        public: Se True, a playlist é pública; caso contrário, privada.

    Returns:
        Playlist criada com os metadados devolvidos pela API.
    """
    # POST /me/playlists é o endpoint actual; /users/{id}/playlists dá 403
    result = client._post(
        "me/playlists",
        payload={"name": name, "public": public, "description": description},
    )
    return Playlist(
        id=result["id"],
        name=result["name"],
        owner=result["owner"]["id"],
        public=result.get("public") or False,
        track_count=0,
        uri=result["uri"],
    )


def add_tracks(
    client: spotipy.Spotify, playlist_id: str, track_uris: list[str]
) -> None:
    """Adiciona faixas a uma playlist em blocos de 100 (limite da API).

    Args:
        client: Cliente Spotify autenticado.
        playlist_id: ID da playlist de destino.
        track_uris: Lista de URIs das faixas a adicionar.
    """
    for i in range(0, len(track_uris), CHUNK_SIZE):
        chunk = track_uris[i : i + CHUNK_SIZE]
        client.playlist_add_items(playlist_id, chunk)


def create_and_populate(
    client: spotipy.Spotify,
    name: str,
    track_uris: list[str],
    description: str = "",
    public: bool = False,
) -> Playlist:
    """Cria uma playlist e adiciona as faixas numa só operação.

    Args:
        client: Cliente Spotify autenticado.
        name: Nome da playlist.
        track_uris: URIs das faixas a adicionar.
        description: Descrição opcional.
        public: Se True, a playlist é pública.

    Returns:
        Playlist criada e populada.
    """
    playlist = create_playlist(client, name, description=description, public=public)
    if track_uris:
        add_tracks(client, playlist.id, track_uris)
        playlist.track_count = len(track_uris)
    return playlist
