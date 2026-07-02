"""Cria a playlist "Férias em Família 2026" no Spotify.

Lê playlists/ferias_familia.json, procura cada faixa no Spotify, cria a
playlist (privada) e adiciona as faixas pela ordem definida. No fim imprime
um resumo com a duração total e as faixas que não foram encontradas.

Uso:
    python create_vacation_playlist.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import spotipy

from src.auth import get_client
from src.playlists import add_tracks, create_playlist, find_playlist_by_name

PLAYLIST_FILE = Path(__file__).resolve().parent / "playlists" / "ferias_familia.json"


def search_track(client: spotipy.Spotify, artist: str, title: str) -> dict | None:
    queries = [
        f'track:"{title}" artist:"{artist}"',
        f"{title} {artist}",
    ]
    for query in queries:
        results = client.search(q=query, type="track", limit=5)
        items = results.get("tracks", {}).get("items", [])
        if items:
            return items[0]
    return None


def format_duration(total_ms: int) -> str:
    minutes = total_ms // 60_000
    return f"{minutes // 60}h{minutes % 60:02d}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="apenas procura as faixas e mostra o resultado, sem criar a playlist",
    )
    args = parser.parse_args()

    data = json.loads(PLAYLIST_FILE.read_text(encoding="utf-8"))
    client = get_client()

    uris: list[str] = []
    missing: list[str] = []
    total_ms = 0

    for block in data["blocks"]:
        print(f"\n{block['title']}")
        for entry in block["tracks"]:
            label = f"{entry['artist']} — {entry['title']}"
            track = search_track(client, entry["artist"], entry["title"])
            if track is None:
                missing.append(label)
                print(f"  ✗ {label}  (não encontrada)")
                continue
            if track["uri"] in uris:
                print(f"  = {label}  (duplicada, ignorada)")
                continue
            uris.append(track["uri"])
            total_ms += track["duration_ms"]
            found = f"{track['artists'][0]['name']} — {track['name']}"
            marker = "✓" if found.lower() == label.lower() else "~"
            print(f"  {marker} {found}")

    print(f"\nEncontradas {len(uris)} faixas · duração total ≈ {format_duration(total_ms)}")
    if missing:
        print("Não encontradas:")
        for label in missing:
            print(f"  - {label}")

    if args.dry_run:
        print("\n(dry-run: playlist não criada)")
        return

    if not uris:
        sys.exit("Nenhuma faixa encontrada; playlist não criada.")

    name = data["name"]
    existing = find_playlist_by_name(client, name)
    if existing is not None:
        sys.exit(
            f'Já existe uma playlist chamada "{name}" ({existing.tracks_total} faixas). '
            "Apaga-a ou renomeia-a no Spotify e volta a correr o script."
        )

    playlist = create_playlist(
        client,
        name=name,
        description=data.get("description", ""),
        public=data.get("public", False),
    )
    added = add_tracks(client, playlist.id, uris)
    print(f'\nPlaylist "{playlist.name}" criada com {added} faixas. Boas férias! 🌴')


if __name__ == "__main__":
    main()
