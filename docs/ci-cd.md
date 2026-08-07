# CI/CD — GitHub Actions

## Vue d’ensemble

```
Push / PR → CI (lint → tests → Docker/Nginx)
                │
Push main / tag v* → CD (build + push image GHCR)
```

| Workflow | Fichier | Déclencheurs |
|----------|---------|--------------|
| **CI** | `.github/workflows/ci.yml` | `push` / `PR` sur `main` & `develop`, manuel |
| **CD** | `.github/workflows/cd.yml` | `push` sur `main`, tags `v*`, manuel |

## Pipeline CI

### 1. Lint
- Python 3.13 + Ruff (`ruff check .`)
- Job rapide, sans services

### 2. Tests
- Services : **PostgreSQL 16** + **Redis 7**
- `manage.py check` + migrations
- `pytest` + couverture (`coverage.xml` en artifact, 14 jours)
- Settings : `config.settings.test` (Postgres si `GITHUB_ACTIONS=true`)

### 3. Docker & Nginx
- Build de l’image `Dockerfile` (cache Buildx GHA)
- `docker compose config` (dev + prod)
- `nginx -t` sur la conf du dépôt
- Smoke import Django dans l’image

Les jobs Docker attendent lint **et** tests (`needs`).

## Pipeline CD

Sur `main` ou tag `v1.2.3` :
1. Login **GHCR** (`ghcr.io`) avec `GITHUB_TOKEN`
2. Build & push des tags :
   - `latest` (branche par défaut)
   - `sha-<short>`
   - version semver si tag `v*`

Image typique :

```text
ghcr.io/<org-ou-user>/apm-platform:latest
ghcr.io/<org-ou-user>/apm-platform:sha-abc1234
```

Pull (dépôt public ou après `docker login ghcr.io`) :

```bash
docker pull ghcr.io/<owner>/apm-platform:latest
```

> Le package peut être privé par défaut : Settings → Packages → Change visibility.

## Concurrence

`concurrency` annule les runs obsolètes sur la même branche (économie de minutes Actions).

## Badge (README)

```markdown
[![CI](https://github.com/<owner>/apm-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/<owner>/apm-platform/actions/workflows/ci.yml)
```

## Exécution locale équivalente

```bash
ruff check .
python -m pytest -q --cov=apps --cov-report=term
docker compose -f docker-compose.yml config --quiet
POSTGRES_PASSWORD=ci-test docker compose -f docker-compose.prod.yml config --quiet
docker build -t apm-platform:local .
```
