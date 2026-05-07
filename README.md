# spotify-playlists

Automatiza criação e gestão de playlists no Spotify via CLI.

## Setup

```bash
git clone https://github.com/RicardoMoey/Spotify.git
cd Spotify
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edita `.env` com as tuas credenciais:

```
SPOTIPY_CLIENT_ID=...
SPOTIPY_CLIENT_SECRET=...
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

## Registo da app Spotify

1. Abre o [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) e cria uma app
2. Em *Settings → Redirect URIs* adiciona exactamente: `http://127.0.0.1:8888/callback`
3. Copia o *Client ID* e *Client Secret* para `.env`

Na primeira execução o browser abre para autorização OAuth. O token fica em cache em `.cache`.

## Comandos

```bash
# Artistas mais frequentes na biblioteca + géneros sugeridos
python cli.py genres

# Gerar uma playlist por critérios
python cli.py generate \
  --genres "dub,reggae" \
  --years 1970-2000 \
  --popularity 10-70 \
  --size 30 \
  --name "Dub Clássico" \
  --exclude-known        # omite faixas já em qualquer playlist

# Gerar várias playlists a partir de ficheiro YAML
python cli.py batch                  # usa playlists.yml
python cli.py batch outro.yml
```

## playlists.yml

```yaml
slug_da_playlist:            # usado como nome se 'name' omitido
  name: "Nome no Spotify"    # opcional
  genres: [post-rock, ambient]
  years: [2010, 2025]
  popularity: [20, 70]       # opcional (0–100)
  size: 40
  exclude_known: true        # opcional, padrão false
  public: false              # opcional, padrão false
  description: "..."         # opcional
```

O campo `exclude_known` indexa a biblioteca uma vez por sessão e reutiliza o índice em todos os entries do mesmo batch.

## Troubleshooting

Erros 403, campos ausentes ou comportamentos inesperados da API Spotify:
→ [`docs/spotify-api-changes.md`](docs/spotify-api-changes.md)
