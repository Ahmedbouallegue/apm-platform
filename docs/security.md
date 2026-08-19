# Sécurité — APM Platform

## Mesures implémentées

| Domaine | Mesure |
|---------|--------|
| **Médias** | `/media/*` servi par Django (`SecureMediaView`) — auth + rôle Lecteur minimum |
| **Swagger / OpenAPI** | `/api/docs/`, `/api/schema/`, `/api/redoc/` — Admin DSI + session |
| **Django Admin** | `/admin/` — Admin DSI uniquement (pas simple `is_staff`) |
| **JWT** | Rotation refresh + blacklist (`token_blacklist`) |
| **Rate limiting** | Login web, JWT, reset password (cache Redis) |
| **API DRF** | Throttling anon/user + `IsAuthenticated` par défaut |
| **Uploads** | Extensions / MIME / taille max (`MAX_UPLOAD_SIZE_BYTES`) |
| **Prometheus** | `/metrics` — IP privée, token `X-Metrics-Token` ou Admin DSI |
| **Headers** | CSP, COOP, Permissions-Policy, X-Frame-Options |
| **Production** | `SECRET_KEY` obligatoire, cookies secure, HSTS (si HTTPS) |

## Variables d'environnement

Voir [`.env.example`](../.env.example) :

- `SECRET_KEY` — **obligatoire** en production (valeur forte unique)
- `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` — activer avec HTTPS
- `LOGIN_RATE_LIMIT_*` — tentatives auth
- `METRICS_TOKEN` — token optionnel pour scraper Prometheus
- `MAX_UPLOAD_SIZE_BYTES` — taille max upload documents

## Déploiement VM / production

1. Copier `.env.example` → `.env` et générer un `SECRET_KEY` fort
2. `POSTGRES_PASSWORD` unique, `DEBUG=False`, `DJANGO_SETTINGS_MODULE=config.settings.production`
3. Terminer TLS devant Nginx (Let's Encrypt) puis `SECURE_SSL_REDIRECT=True`
4. Ne pas exposer Postgres/Redis publiquement (`docker-compose.prod.yml` OK)
5. Comptes Lecteur : jamais `is_superuser` / `is_staff`

## Limites connues

- **CSP** : `'unsafe-inline'` requis pour scripts inline actuels
- **Rate limit** : par IP — contournable via proxy distribué (ajouter WAF si besoin)

## Tests

```bash
python -m pytest apps/core/tests/test_security.py -q
```
