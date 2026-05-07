# spotify-playlists

Automatiza playlists do Spotify com Python e [spotipy](https://spotipy.readthedocs.io/).

## Setup

### 1. Credenciais Spotify

1. Acede ao [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Cria uma aplicação e copia o **Client ID** e **Client Secret**
3. Adiciona `http://localhost:8888/callback` como Redirect URI

### 2. Variáveis de ambiente

```bash
cp .env.example .env
# edita .env com as tuas credenciais
```

### 3. Ambiente virtual e dependências

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

Na primeira execução abrirá o browser para autorização. O token fica em cache em `.cache`.

## Estrutura

```
src/
  auth.py       # OAuth — get_client()
  playlists.py  # Dataclass Playlist + CRUD helpers
main.py         # Ponto de entrada
```
