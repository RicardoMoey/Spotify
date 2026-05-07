"""Interface de linha de comandos para gestão de playlists Spotify."""

from __future__ import annotations

import argparse
import logging
import sys

import spotipy

from src.auth import get_client
from src.discovery import analyze_library_genres, collect_library_uris, search_tracks_by_criteria
from src.playlists import create_and_populate

logging.basicConfig(level=logging.INFO, format="  %(message)s")
# Silencia os logs verbosos de HTTP do spotipy (erros 4xx/5xx)
logging.getLogger("spotipy.client").setLevel(logging.CRITICAL)
logger = logging.getLogger(__name__)


def cmd_genres(sp: spotipy.Spotify) -> None:
    """Mostra os artistas mais frequentes e sugere géneros para usar em 'generate'."""
    from src.playlists import list_user_playlists

    print("A analisar biblioteca (pode demorar alguns segundos)...\n")
    try:
        artists = analyze_library_genres(sp)
        playlists = list_user_playlists(sp)
    except spotipy.SpotifyException as exc:
        print(f"Erro ao aceder à API: {exc}", file=sys.stderr)
        sys.exit(1)

    # Sugestões de géneros a partir dos nomes das playlists
    # Exclui nomes longos (títulos de filmes/séries) ou com " - " (compilações)
    playlist_genres = [
        pl.name.strip()
        for pl in playlists
        if pl.name.strip() and " - " not in pl.name and len(pl.name) <= 25
    ]
    if playlist_genres:
        print("Géneros sugeridos (nomes das tuas playlists):")
        print("  " + ", ".join(f'"{g}"' for g in playlist_genres))
        print()

    if not artists:
        print("Não foi possível ler artistas das playlists.")
        print("Nota: playlists seguidas (não criadas por ti) estão inacessíveis via API.")
        return

    print(f"{'#':<4} {'Artista':<42} {'Playlists':>9}")
    print("-" * 57)
    for i, (artist, count) in enumerate(list(artists.items())[:30], start=1):
        print(f"{i:<4} {artist[:41]:<42} {count:>9}")

    print(f"\n{len(artists)} artistas únicos nas playlists acessíveis.")
    print("\nNota: dados de géneros da API Spotify indisponíveis desde Nov 2024")
    print("para apps em desenvolvimento. Usa os géneros acima em 'generate'.")


def cmd_generate(sp: spotipy.Spotify, args: argparse.Namespace) -> None:
    """Gera uma playlist temática com base nos critérios fornecidos."""
    genres: list[str] | None = None
    if args.genres:
        genres = [g.strip() for g in args.genres.split(",") if g.strip()]

    year_range: tuple[int, int] | None = None
    if args.years:
        try:
            start_s, end_s = args.years.split("-", 1)
            year_range = (int(start_s), int(end_s))
        except ValueError:
            print("Formato de anos inválido. Usa: --years 2015-2025", file=sys.stderr)
            sys.exit(1)

    popularity_range: tuple[int, int] | None = None
    if args.popularity:
        try:
            low_s, high_s = args.popularity.split("-", 1)
            popularity_range = (int(low_s), int(high_s))
        except ValueError:
            print("Formato de popularidade inválido. Usa: --popularity 10-60", file=sys.stderr)
            sys.exit(1)

    if not genres and not year_range:
        print("Fornece pelo menos --genres ou --years.", file=sys.stderr)
        sys.exit(1)

    print("A pesquisar faixas...\n")
    try:
        tracks = search_tracks_by_criteria(
            sp,
            genres=genres,
            year_range=year_range,
            popularity_range=popularity_range,
            limit=args.size,
        )
    except ValueError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)
    except spotipy.SpotifyException as exc:
        print(f"Erro na API do Spotify: {exc}", file=sys.stderr)
        sys.exit(1)

    if not tracks:
        print(
            "Nenhuma faixa encontrada com esses critérios.\n"
            "Sugestões: alarga o intervalo de anos, remove filtros de popularidade "
            "ou experimenta géneros mais abrangentes."
        )
        sys.exit(0)

    if args.exclude_known:
        print("A indexar biblioteca para exclusão de duplicados...")
        try:
            known_uris = collect_library_uris(sp)
        except spotipy.SpotifyException as exc:
            print(f"Erro ao ler biblioteca: {exc}", file=sys.stderr)
            sys.exit(1)

        before = len(tracks)
        tracks = [t for t in tracks if t["uri"] not in known_uris]
        excluded = before - len(tracks)
        logger.info(
            "%d track(s) excluída(s) (já presentes na biblioteca), %d track(s) novas",
            excluded, len(tracks),
        )
        print(f"  {excluded} excluída(s) (já na biblioteca), {len(tracks)} nova(s).\n")

        if not tracks:
            print("Nenhuma faixa nova encontrada. Tenta alargar os critérios.")
            sys.exit(0)

        if len(tracks) < args.size:
            print(
                f"Aviso: apenas {len(tracks)} faixa(s) novas disponíveis "
                f"(pediste {args.size}). A prosseguir com o que há.\n"
            )

    print(f"{len(tracks)} faixa(s) encontrada(s). Pré-visualização:\n")
    print(f"{'#':<4} {'Nome':<40} {'Artistas':<26} {'Ano':>4} {'Pop':>4}")
    print("-" * 82)
    for i, t in enumerate(tracks[:10], start=1):
        name = t["name"][:39]
        artists = ", ".join(t["artists"])[:25]
        pop = "N/A" if t["popularity"] == -1 else str(t["popularity"])
        print(f"{i:<4} {name:<40} {artists:<26} {t['release_year']:>4} {pop:>4}")

    if len(tracks) > 10:
        print(f"  ... e mais {len(tracks) - 10} faixa(s)")

    print(f"\nCriar playlist \"{args.name}\" com {len(tracks)} faixa(s)? [y/N] ", end="", flush=True)
    try:
        answer = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelado.")
        sys.exit(0)

    if answer != "y":
        print("Cancelado.")
        sys.exit(0)

    print("\nA criar playlist...")
    try:
        playlist = create_and_populate(
            sp,
            name=args.name,
            track_uris=[t["uri"] for t in tracks],
            description=args.description,
            public=args.public,
        )
    except spotipy.SpotifyException as exc:
        print(f"Erro ao criar playlist: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\nPlaylist criada com sucesso!")
    print(f"  Nome:    {playlist.name}")
    print(f"  Faixas:  {playlist.track_count}")
    print(f"  URI:     {playlist.uri}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Automatizador de playlists Spotify",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "genres",
        help="Analisa os géneros da tua biblioteca (top 30)",
    )

    gen = subparsers.add_parser(
        "generate",
        help="Gera uma playlist temática por pesquisa",
    )
    gen.add_argument(
        "--genres",
        metavar="G",
        help='Géneros separados por vírgula, ex: "indie,experimental hip hop"',
    )
    gen.add_argument(
        "--years",
        metavar="YYYY-YYYY",
        help="Intervalo de anos, ex: 2015-2025",
    )
    gen.add_argument(
        "--popularity",
        metavar="N-N",
        help="Intervalo de popularidade (0-100), ex: 10-60",
    )
    gen.add_argument(
        "--size",
        type=int,
        default=30,
        metavar="N",
        help="Número de faixas a incluir (padrão: 30)",
    )
    gen.add_argument("--name", required=True, help="Nome da playlist a criar")
    gen.add_argument("--description", default="", help="Descrição da playlist")
    gen.add_argument("--public", action="store_true", help="Torna a playlist pública")
    gen.add_argument(
        "--exclude-known",
        action="store_true",
        dest="exclude_known",
        help="Remove faixas já presentes nalguma playlist da biblioteca",
    )

    args = parser.parse_args()
    sp = get_client()

    if args.command == "genres":
        cmd_genres(sp)
    elif args.command == "generate":
        cmd_generate(sp, args)


if __name__ == "__main__":
    main()
