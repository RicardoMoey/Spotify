from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator

import spotipy


@dataclass(frozen=True)
class Playlist:
    id: str
    name: str
    owner: str
    tracks_total: int
    public: bool | None
    collaborative: bool

    @classmethod
    def from_api(cls, item: dict) -> "Playlist":
        return cls(
            id=item["id"],
            name=item["name"],
            owner=item["owner"]["display_name"] or item["owner"]["id"],
            tracks_total=item["tracks"]["total"],
            public=item.get("public"),
            collaborative=item.get("collaborative", False),
        )


def list_user_playlists(client: spotipy.Spotify, limit: int = 50) -> Iterator[Playlist]:
    offset = 0
    while True:
        page = client.current_user_playlists(limit=limit, offset=offset)
        items = page.get("items", [])
        if not items:
            return
        for item in items:
            yield Playlist.from_api(item)
        if page.get("next") is None:
            return
        offset += len(items)


def find_playlist_by_name(
    client: spotipy.Spotify, name: str
) -> Playlist | None:
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
    me = client.current_user()
    created = client.user_playlist_create(
        user=me["id"],
        name=name,
        public=public,
        description=description,
    )
    return Playlist.from_api(created)


def add_tracks(
    client: spotipy.Spotify,
    playlist_id: str,
    track_uris: Iterable[str],
) -> int:
    uris = list(track_uris)
    added = 0
    for i in range(0, len(uris), 100):
        chunk = uris[i : i + 100]
        client.playlist_add_items(playlist_id, chunk)
        added += len(chunk)
    return added
