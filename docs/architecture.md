# Architecture — APM Platform

## Principes

1. **Monolithe modulaire** : une app Django = un bounded context.
2. **Vues minces** : HTTP dans `views`, logique dans `services`, lectures complexes dans `selectors`.
3. **Settings éclatés** : `base` / `development` / `production` / `test`.
4. **12-factor** : configuration via variables d’environnement.
5. **Observabilité** : healthcheck, métriques Prometheus, logs structurés (baseline).
6. **CI/CD** : GitHub Actions — lint/tests/Docker (CI) + publication GHCR (CD). Voir [`ci-cd.md`](ci-cd.md).

## Couches

| Couche | Emplacement | Rôle |
|--------|-------------|------|
| Présentation | `views`, `serializers`, `urls` | API REST |
| Application | `services`, `tasks` | Cas d’usage, async |
| Domaine | `models` | Entités & règles |
| Infrastructure | PostgreSQL, Redis, Celery, Nginx | Technique |

## Décisions Sprint 0

- User custom : `apps.accounts.User` (`AUTH_USER_MODEL`)
- Auth API : JWT Bearer (Simple JWT)
- Docs : `/api/docs/` (Swagger UI)
- Async : Celery worker + beat
- Entrée HTTP : Nginx → Gunicorn (voir [`docker.md`](docker.md))
- Compose : `docker-compose.yml` (dev) / `docker-compose.prod.yml` (prod)
