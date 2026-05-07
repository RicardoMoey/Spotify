"""Ponto de entrada: autentica e lista as playlists do utilizador."""

from src.auth import get_client
from src.playlists import list_user_playlists


def main() -> None:
    """Autentica com o Spotify e imprime as playlists do utilizador."""
    print("A autenticar com o Spotify...")
    client = get_client()

    user = client.current_user()
    print(f"Ligado como: {user['display_name']} ({user['id']})\n")

    playlists = list_user_playlists(client)

    if not playlists:
        print("Nenhuma playlist encontrada.")
        return

    print(f"{'#':<4} {'Nome':<50} {'Faixas':>6}  {'Visib.'}")
    print("-" * 70)
    for i, pl in enumerate(playlists, start=1):
        visibility = "pública" if pl.public else "privada"
        print(f"{i:<4} {pl.name[:49]:<50} {pl.track_count:>6}  {visibility}")

    print(f"\nTotal: {len(playlists)} playlist(s)")


if __name__ == "__main__":
    main()
