# Mudanças à API Spotify (Novembro 2024)

Em Novembro de 2024 a Spotify restringiu o acesso a vários endpoints e removeu campos de resposta para aplicações em modo desenvolvimento (não verificadas). As mudanças abaixo foram descobertas empiricamente ao construir este projecto.

## Tabela de mudanças

| Endpoint / Campo | Comportamento anterior | Comportamento actual | Onde foi descoberto |
|---|---|---|---|
| `playlist["tracks"]["total"]` | Campo com contagem de faixas | Campo renomeado para `playlist["items"]["total"]` | `main.py` mostrava 0 faixas em todas as playlists após a primeira execução |
| `item["track"]` (itens de playlist) | Cada item de playlist tinha chave `track` | Chave renomeada para `item` | `analyze_library_genres` recolhia 0 artistas de playlists com faixas |
| `GET /v1/artists?ids=…` (batch) | Devolvia géneros de até 50 artistas por chamada | Retorna 403 Forbidden | `analyze_library_genres` falhou ao tentar o lookup em batch |
| Campo `genres` nos objectos artista | Populado via `search` ou `artist()` | Retorna `None` ou `[]` independentemente do endpoint | `sp.artist()` e `search type=artist` testados directamente — sem dados de género |
| `genre:` no search — `limit` | Aceitava até 50 resultados por página | Máximo de 10 resultados por página; acima disso retorna 400 "Invalid limit" | `search_tracks_by_criteria` falhava com `limit=50` em qualquer query com `genre:` |
| `genre:X OR genre:Y` no search | OR entre filtros de género funcionava | Retorna sempre 0 resultados; OR é ignorado silenciosamente | `generate` com dois géneros devolvia 0 faixas apesar de cada género individualmente ter resultados |
| Campo `popularity` no search com `genre:` | Presente nos objectos track | Campo ausente da resposta; `.get("popularity")` retorna `None` | Filtro de popularidade eliminava 100% das faixas em queries com `genre:` |
| `POST /v1/users/{user_id}/playlists` | Criava playlists para o utilizador | Retorna 403 Forbidden; endpoint deprecado | `create_playlist` falhava ao tentar criar a primeira playlist temática |

## Workarounds implementados

- **`items` vs `tracks`**: leitura com fallback duplo — `item.get("items") or item.get("tracks")`.
- **`item` vs `track`**: leitura com fallback duplo — `entry.get("item") or entry.get("track")`.
- **batch artists**: substituído por `sp.artist()` individual; sem dados de género disponíveis.
- **géneros**: `analyze_library_genres` redesenhado para devolver frequência de artistas; géneros são inferidos dos nomes das playlists do utilizador.
- **`limit=10`**: `search_tracks_by_criteria` usa `page_size=10` quando a query contém `genre:`, e 50 caso contrário.
- **OR entre géneros**: cada género é pesquisado separadamente; resultados são combinados com deduplicação por URI.
- **`popularity` ausente**: o filtro de popularidade só é aplicado se o campo estiver presente (`!= None`); faixas sem dados de popularidade são incluídas.
- **criação de playlists**: substituído `POST /users/{id}/playlists` por `POST /me/playlists` via `client._post("me/playlists", ...)`.
