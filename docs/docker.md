# Conteneurisation Docker & Nginx

## Schéma

```
Navigateur
    │
    ▼
 Nginx :80  ──► /static /media (volumes)
    │
    ▼
 Gunicorn :8000 (Django / DRF)
    ├── PostgreSQL :5432
    └── Redis :6379 ──► Celery worker + beat
```

## Fichiers

| Fichier | Rôle |
|---------|------|
| `Dockerfile` | Image multi-stage Python 3.13 + Gunicorn (utilisateur non-root) |
| `docker/entrypoint.sh` | Attente PostgreSQL, migrations, `collectstatic` |
| `docker-compose.yml` | Stack **développement** (bind-mount, `--reload`, ports DB/Redis) |
| `docker-compose.prod.yml` | Stack **production** (image figée, seuls Nginx exposé) |
| `docker/nginx/` | Reverse-proxy, gzip, cache static, en-têtes sécurité |

## Démarrage (développement)

```bash
cp .env.example .env
docker compose up --build -d
```

| Service | URL |
|---------|-----|
| Application (Nginx) | http://localhost/ |
| Gunicorn direct | http://localhost:8000/ |
| Health | http://localhost/api/health/ |

Observabilité (optionnelle) :

```bash
docker compose --profile observability up -d
```

## Démarrage (production)

```bash
cp .env.example .env
# Renseigner SECRET_KEY, POSTGRES_PASSWORD, DEBUG=False, ALLOWED_HOSTS=…
docker compose -f docker-compose.prod.yml up --build -d
```

- Postgres, Redis et Gunicorn **ne sont pas** publiés sur l’hôte.
- Nginx sert `/static/` et `/media/` depuis les volumes partagés.
- Derrière TLS : `SECURE_SSL_REDIRECT=True`, cookies secure, `SECURE_HSTS_SECONDS=31536000`.

## Commandes utiles

```bash
# Logs
docker compose logs -f web nginx

# Migrations manuelles
docker compose exec web python manage.py migrate

# Collectstatic (après changement CSS/JS en dev)
docker compose exec web python manage.py collectstatic --noinput

# Shell
docker compose exec web python manage.py shell

# Arrêt
docker compose down
# + volumes (attention données) :
docker compose down -v
```

## Nginx

- Reverse-proxy HTTP/1.1 + keepalive vers `web:8000`
- Gzip (HTML/CSS/JS/JSON)
- Cache long pour `/static/`, court pour `/media/`
- En-têtes : `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`
- `server_tokens off`, corps max 25 Mo

## Entrypoint

Variables :

| Variable | Défaut | Effet |
|----------|--------|--------|
| `RUN_MIGRATIONS` | `0` | `1` = `migrate --noinput` (web) |
| `RUN_COLLECTSTATIC` | `0` | `1` = `collectstatic` (web) |
| `SKIP_DB_WAIT` | `0` | `1` = ne pas attendre PostgreSQL |

Worker et beat gardent `RUN_MIGRATIONS=0` / `RUN_COLLECTSTATIC=0`.
