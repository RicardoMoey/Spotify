from __future__ import annotations

from src.auth import get_client
from src.playlists import list_user_playlists


def main() -> None:
    client = get_client()
    me = client.current_user()
    print(f"Authenticated as: {me['display_name']} ({me['id']})\n")

    print("Your playlists:")
    count = 0
    for playlist in list_user_playlists(client):
        owned = " (owned)" if playlist.owner == me["display_name"] else ""
        print(f"  - {playlist.name} [{playlist.tracks_total} tracks]{owned}")
        count += 1

    print(f"\nTotal: {count} playlists")


if __name__ == "__main__":
    main()
