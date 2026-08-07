# Plateforme de Gestion du Patrimoine Applicatif (APM) — DSI

API REST professionnelle pour inventorier, gouverner et piloter le patrimoine applicatif.

## Stack

| Couche | Technologie |
|--------|-------------|
| Backend | Python 3.13, Django 5, Django REST Framework |
| Auth | JWT (Simple JWT) |
| Base de données | PostgreSQL 16 |
| Async | Celery + Redis |
| Docs API | Swagger / OpenAPI (`drf-spectacular`) |
| Conteneurs | Docker, Docker Compose, Nginx |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus + Grafana |

## Architecture

Monolithe modulaire Django (Clean Architecture adaptée) :

- `config/` — settings, URLs, WSGI/ASGI, Celery
- `apps/` — bounded contexts métier (applications, serveurs, certificats, …)
- Chaque app : `models` / `serializers` / `views` / `services` / `selectors` / `tasks`
- Documentation : [`docs/architecture.md`](docs/architecture.md), [`docs/guide-utilisateur.md`](docs/guide-utilisateur.md)

```
Client → Nginx → Gunicorn (Django/DRF) → Services → PostgreSQL
                              ↘ Celery ← Redis
```

## Interface web (Topnet)

Design pro/sérieux aux couleurs Topnet (navy / cyan / orange) :

| Page | URL |
|------|-----|
| Connexion | http://localhost:8000/login/ |
| Tableau de bord | http://localhost:8000/ |
| Gestion utilisateurs | http://localhost:8000/users/ |
| Certificats SSL | http://localhost:8000/certificates/ |
| Domaines | http://localhost:8000/domains/ |
| Fournisseurs | http://localhost:8000/vendors/ |
| Contrats | http://localhost:8000/contracts/ |

Créer un administrateur :

```bash
python manage.py migrate
python manage.py bootstrap_admin --username admin --password 'Admin123!' --email admin@topnet.tn
python manage.py runserver
```

### API utilisateurs (JWT)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/auth/me/` | Profil connecté |
| GET/POST | `/api/auth/users/` | Liste / création |
| GET/PATCH/DELETE | `/api/auth/users/{id}/` | Détail / maj / désactivation |
| POST | `/api/auth/users/{id}/activate/` | Réactivation |
| POST | `/api/auth/users/{id}/deactivate/` | Désactivation |

Rôles : `admin`, `dsi`, `manager` (lecture), `viewer`.

## Prérequis

- Docker & Docker Compose
- (optionnel) Python 3.13 + Git pour le développement hors Docker

## Démarrage rapide (Docker)

```bash
cp .env.example .env
docker compose up --build -d
```

Après modification de fichiers dans `static/` (CSS/JS), régénérer les assets servis par Nginx :

```bash
docker compose exec web python manage.py collectstatic --noinput
```

Puis hard-refresh navigateur (Ctrl+F5).

Services exposés :

| Service | URL |
|---------|-----|
| API via Nginx | http://localhost/ |
| API directe | http://localhost:8000/ |
| Swagger | http://localhost:8000/api/docs/ |
| ReDoc | http://localhost:8000/api/redoc/ |
| Health | http://localhost:8000/api/health/ |
| Admin | http://localhost:8000/admin/ |
| Prometheus | http://localhost:9090/ |
| Grafana | http://localhost:3000/ (admin/admin) |

Créer un superutilisateur :

```bash
docker compose exec web python manage.py createsuperuser
```

Obtenir un token JWT :

```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"votre_mot_de_passe"}'
```

## Développement local (sans Docker pour l’app)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements/development.txt
cp .env.example .env
# Ajuster DATABASE_URL / REDIS_URL vers localhost
python manage.py migrate
python manage.py runserver
celery -A config worker -l info
```

## Applications Django

| App | Domaine |
|-----|---------|
| `core` | Bases partagées, health |
| `accounts` | Utilisateurs, rôles, JWT |
| `applications` | Catalogue applicatif |
| `technologies` | Stack technique |
| `environments` | DEV / RECETTE / PREPROD / PROD |
| `servers` | Serveurs |
| `certificates` | Certificats SSL |
| `domains` | Noms de domaine |
| `vendors` | Fournisseurs |
| `contracts` | Contrats de maintenance |
| `documents` | Documents |
| `incidents` | Incidents |
| `dependencies` | Dépendances applicatives |
| `notifications` | Notifications |
| `audit` | Logs d’audit |
| `dashboard` | KPIs / tableaux de bord |

Voir `.env.example`. Ne jamais committer `.env`.

## Qualité & CI

```bash
ruff check .
pytest
```

Le workflow GitHub Actions (`.github/workflows/ci.yml`) exécute lint, checks Django, tests et build Docker.

## Structure du dépôt

```
apm-platform/
├── apps/                 # Applications métier
├── config/               # Projet Django
│   └── settings/         # base / development / production / test
├── docker/               # Nginx, Prometheus, Grafana
├── requirements/         # Dépendances Python
├── .github/workflows/    # CI/CD
├── Dockerfile
├── docker-compose.yml
├── manage.py
└── README.md
```

## Sprint 0

Socle technique prêt : architecture, apps, Docker, Redis, Celery, Nginx, DRF, JWT, Swagger, env, CI.

Les modèles métier détaillés et les cas d’usage APM arrivent dans les sprints suivants.

## Licence

Projet académique — PFE DSI.
