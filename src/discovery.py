"""Descoberta de músicas e análise de géneros da biblioteca."""

from __future__ import annotations

import logging

import spotipy

from .playlists import list_user_playlists

logger = logging.getLogger(__name__)


def search_tracks_by_criteria(
    sp: spotipy.Spotify,
    genres: list[str] | None = None,
    year_range: tuple[int, int] | None = None,
    popularity_range: tuple[int, int] | None = None,
    market: str = "PT",
    limit: int = 50,
) -> list[dict]:
    """Pesquisa faixas combinando géneros, intervalo de anos e popularidade.

    Constrói uma query Spotify com genre:"..." e year:YYYY-YYYY,
    pagina os resultados e aplica filtro de popularidade.

    Args:
        sp: Cliente Spotify autenticado.
        genres: Géneros a pesquisar, unidos com OR na query.
        year_range: Tuplo (início, fim) de anos, inclusive.
        popularity_range: Tuplo (min, max) de popularidade (0-100).
        market: Código ISO do mercado para disponibilidade.
        limit: Máximo de faixas a devolver após filtros.

    Returns:
        Lista de dicts com id, uri, name, artists, album, release_year, popularity.

    Raises:
        ValueError: Se nenhum critério for fornecido.
        spotipy.SpotifyException: Em caso de erro na API do Spotify.
    """
    if not genres and not year_range:
        raise ValueError("Fornece pelo menos um critério: géneros ou intervalo de anos.")

    # A API Spotify não suporta OR entre genre:, e aceita max 10 resultados
    # por página em queries com genre:. Pesquisamos cada género separadamente.
    genre_list = genres if genres else [None]
    year_part = f" year:{year_range[0]}-{year_range[1]}" if year_range else ""

    collected: list[dict] = []
    seen_uris: set[str] = set()
    per_genre = max((limit * 3) // len(genre_list), limit)  # margem para filtros

    for genre in genre_list:
        query = (f'genre:"{genre}"' if genre else "") + year_part
        query = query.strip()
        page_size = 10 if genre else 50
        logger.info("Query: %s", query)

        offset = 0
        page = 0
        genre_collected = 0

        while genre_collected < per_genre:
            page += 1
            logger.info("Género '%s' — página %d (%d recolhidas)", genre or "*", page, len(collected))

            try:
                result = sp.search(q=query, type="track", market=market, limit=page_size, offset=offset)
            except spotipy.SpotifyException as exc:
                logger.error("Erro na pesquisa Spotify: %s", exc)
                raise

            tracks_page = result.get("tracks", {})
            items = tracks_page.get("items") or []
            total_available = tracks_page.get("total", 0)

            if not items:
                logger.info("Sem mais resultados para '%s'.", genre or "*")
                break

            for track in items:
                if not track:
                    continue
                uri = track.get("uri", "")
                if not uri or uri in seen_uris:
                    continue
                seen_uris.add(uri)

                popularity = track.get("popularity")  # pode ser None em queries genre:
                if popularity_range and popularity is not None:
                    if not (popularity_range[0] <= popularity <= popularity_range[1]):
                        continue

                release_date = (track.get("album") or {}).get("release_date", "0000")
                try:
                    release_year = int(release_date[:4])
                except (ValueError, IndexError):
                    release_year = 0

                collected.append({
                    "id": track["id"],
                    "uri": uri,
                    "name": track["name"],
                    "artists": [a["name"] for a in track.get("artists") or []],
                    "album": (track.get("album") or {}).get("name", ""),
                    "release_year": release_year,
                    "popularity": popularity if popularity is not None else -1,
                })
                genre_collected += 1

            offset += page_size
            if offset >= min(total_available, 1000):
                logger.info("Paginação esgotada para '%s' (%d disponíveis).", genre or "*", total_available)
                break

    logger.info("Faixas recolhidas: %d", len(collected))
    return collected[:limit]


def collect_library_uris(sp: spotipy.Spotify) -> set[str]:
    """Recolhe todos os URIs de faixas presentes nas playlists do utilizador.

    Usa o parâmetro fields para pedir apenas URIs, minimizando o payload.
    Playlists inacessíveis (403) são ignoradas com aviso.

    Args:
        sp: Cliente Spotify autenticado.

    Returns:
        Conjunto de URIs de faixas (spotify:track:…) encontrados na biblioteca.
    """
    playlists = list_user_playlists(sp)
    logger.info("A indexar URIs de %d playlist(s)...", len(playlists))

    known: set[str] = set()

    for pl in playlists:
        offset = 0
        while True:
            try:
                response = sp.playlist_items(
                    pl.id,
                    fields="items(item(uri),track(uri)),next",
                    limit=50,
                    offset=offset,
                )
            except spotipy.SpotifyException as exc:
                logger.warning("Sem acesso a '%s' (ignorada): HTTP %s", pl.name, exc.http_status)
                break

            for entry in response.get("items") or []:
                track = entry.get("item") or entry.get("track")
                if not track:
                    continue
                uri = track.get("uri", "")
                if uri.startswith("spotify:track:"):
                    known.add(uri)

            if not response.get("next"):
                break
            offset += 50

    logger.info("%d URIs indexados na biblioteca.", len(known))
    return known


def analyze_library_genres(sp: spotipy.Spotify) -> dict[str, int]:
    """Analisa a biblioteca do utilizador e devolve artistas por frequência.

    Nota: a partir de Nov 2024 a API Spotify não devolve dados de géneros
    para apps em modo desenvolvimento. Esta função recolhe artistas únicos
    das playlists acessíveis e conta quantas vezes cada um aparece.

    Args:
        sp: Cliente Spotify autenticado.

    Returns:
        Dict artista → nº de aparições, ordenado do mais para o menos frequente.
        Playlists inacessíveis (403) são ignoradas com aviso.
    """
    playlists = list_user_playlists(sp)
    logger.info("A analisar %d playlist(s)...", len(playlists))

    artist_counts: dict[str, int] = {}
    accessible = 0

    for pl in playlists:
        offset = 0
        pl_artists: set[str] = set()

        while True:
            try:
                response = sp.playlist_items(
                    pl.id,
                    fields="items(item(artists(name)),track(artists(name))),next",
                    limit=50,
                    offset=offset,
                )
            except spotipy.SpotifyException as exc:
                logger.warning("Sem acesso a '%s' (ignorada): HTTP %s", pl.name, exc.http_status)
                break

            for entry in response.get("items") or []:
                track = entry.get("item") or entry.get("track")
                if not track:
                    continue
                for artist in track.get("artists") or []:
                    name = artist.get("name")
                    if name:
                        pl_artists.add(name)

            if not response.get("next"):
                accessible += 1
                break
            offset += 50

        for name in pl_artists:
            artist_counts[name] = artist_counts.get(name, 0) + 1

        if pl_artists:
            logger.info("'%s': %d artistas únicos", pl.name, len(pl_artists))

    logger.info("%d/%d playlists acessíveis; %d artistas únicos", accessible, len(playlists), len(artist_counts))
    return dict(sorted(artist_counts.items(), key=lambda x: x[1], reverse=True))
