# Guide Monitoring — Prometheus & Grafana

## Architecture de monitoring

```
┌──────────────┐     scrape /metrics      ┌──────────────┐     datasource     ┌──────────────┐
│  Django App  │◄─────── (15s) ──────────│  Prometheus  │──────────────────▶ │   Grafana    │
│  (apm-web)   │                          │  :9090       │                    │   :3000      │
└──────────────┘                          └──────────────┘                    └──────────────┘
                                                ▲
┌──────────────┐     scrape :9100         │
│ Node Exporter│◄─────── (15s) ───────────┘
│  (VM metrics)│
└──────────────┘
```

### Composants

| Composant | Rôle | Port | Image Docker |
|-----------|------|------|--------------|
| **django_prometheus** | Expose les métriques Django sur `/metrics` | 8000 | (intégré à apm-web) |
| **Prometheus** | Collecte et stocke les métriques (scrape) | 9090 | `prom/prometheus:v2.54.1` |
| **Grafana** | Visualisation et dashboards | 3000 | `grafana/grafana:11.2.0` |
| **Node Exporter** | Expose CPU/RAM/disque de la VM | 9100 | `prom/node-exporter` |

---

## 1. Configuration — Fichiers du projet

### 1.1 Docker Compose

Les services Prometheus et Grafana sont dans `docker-compose.yml` sous le profil **observability** :

```yaml
prometheus:
  image: prom/prometheus:v2.54.1
  container_name: apm-prometheus
  restart: unless-stopped
  profiles: ["observability"]
  ports:
    - "${PROMETHEUS_PORT:-9090}:9090"
  volumes:
    - ./docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - prometheus_data:/prometheus
  depends_on:
    - web

grafana:
  image: grafana/grafana:11.2.0
  container_name: apm-grafana
  restart: unless-stopped
  profiles: ["observability"]
  ports:
    - "${GRAFANA_PORT:-3000}:3000"
  environment:
    GF_SECURITY_ADMIN_USER: ${GRAFANA_ADMIN_USER:-admin}
    GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin}
  volumes:
    - grafana_data:/var/lib/grafana
    - ./docker/grafana/provisioning:/etc/grafana/provisioning:ro
  depends_on:
    - prometheus
```

> **Note** : le profil `observability` signifie que ces services ne démarrent pas avec un simple `docker compose up`. Il faut ajouter `--profile observability`.

### 1.2 Prometheus — Configuration de scrape

Fichier : `docker/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s        # fréquence de collecte
  evaluation_interval: 15s    # fréquence d'évaluation des règles

scrape_configs:
  # Prometheus se scrape lui-même
  - job_name: prometheus
    static_configs:
      - targets: ["localhost:9090"]

  # Métriques Django (django_prometheus)
  - job_name: apm-web
    metrics_path: /metrics
    static_configs:
      - targets: ["web:8000"]    # nom du service Docker

  # Métriques système de la VM (node_exporter)
  - job_name: node
    static_configs:
      - targets: ["192.168.88.134:9100"]   # IP de la VM
```

### 1.3 Grafana — Datasource auto-provisionnée

Fichier : `docker/grafana/provisioning/datasources/datasource.yml`

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090    # réseau Docker interne
    isDefault: true
    editable: true
```

### 1.4 Django — Endpoint /metrics

L'app Django expose automatiquement des métriques via `django_prometheus` :

- **Middleware** : `PrometheusBeforeMiddleware` et `PrometheusAfterMiddleware` dans `config/settings/base.py`
- **URL** : `path("", include("django_prometheus.urls"))` dans `config/urls.py`
- **Protection** : `MetricsAccessMiddleware` dans `apps/core/middleware.py` — accès limité aux IP privées, token `X-Metrics-Token`, ou Admin DSI

### 1.5 Variables d'environnement

À configurer dans le fichier `.env` :

| Variable | Défaut | Description |
|----------|--------|-------------|
| `PROMETHEUS_PORT` | `9090` | Port externe Prometheus |
| `GRAFANA_PORT` | `3000` | Port externe Grafana |
| `GRAFANA_ADMIN_USER` | `admin` | Utilisateur admin Grafana |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | Mot de passe admin Grafana |
| `METRICS_TOKEN` | _(vide)_ | Token optionnel pour scraper `/metrics` |
| `METRICS_ALLOWED_IPS` | `127.0.0.1,::1` | IPs autorisées à accéder `/metrics` |

---

## 2. Déploiement sur la VM

### 2.1 Configurer le `.env`

```bash
cd ~/Desktop/apm-platform
nano .env
```

Ajouter :

```env
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=Admin123!
METRICS_TOKEN=mon-token-prometheus-secret
```

### 2.2 Démarrer les services

```bash
sudo docker compose --profile observability up -d
```

### 2.3 Vérifier que tout tourne

```bash
sudo docker compose --profile observability ps
```

Résultat attendu :

```
NAME             IMAGE                      STATUS
apm-prometheus   prom/prometheus:v2.54.1    Up
apm-grafana      grafana/grafana:11.2.0     Up
```

### 2.4 Installer Node Exporter (métriques VM)

```bash
sudo docker run -d \
  --name node-exporter \
  --restart unless-stopped \
  --net="host" \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  prom/node-exporter:latest \
  --path.rootfs=/host
```

Vérifier :

```bash
curl http://localhost:9100/metrics | head -5
```

---

## 3. Accès aux interfaces

| Interface | URL | Identifiants |
|-----------|-----|-------------|
| **Prometheus** | `http://192.168.88.134:9090` | _(pas d'auth)_ |
| **Grafana** | `http://192.168.88.134:3000` | `admin` / `Admin123!` |
| **Django /metrics** | `http://192.168.88.134:8000/metrics` | Accès privé ou token |

---

## 4. Prometheus — Utilisation

### 4.1 Vérifier les targets

- Ouvrir `http://192.168.88.134:9090`
- Menu **Status** → **Targets**
- Tous les targets doivent être **UP** (vert)

| Target | Endpoint | Description |
|--------|----------|-------------|
| `prometheus` | `localhost:9090/metrics` | Prometheus lui-même |
| `apm-web` | `web:8000/metrics` | Métriques Django |
| `node` | `192.168.88.134:9100/metrics` | Métriques VM |

### 4.2 Tester une requête

- Menu **Graph**
- Taper dans le champ : `django_http_requests_total_by_method_total`
- Cliquer **Execute**
- Onglet **Graph** pour voir la courbe

### 4.3 Métriques Django disponibles

| Métrique | Description |
|----------|-------------|
| `django_http_requests_total_by_method_total` | Nombre total de requêtes par méthode (GET, POST...) |
| `django_http_responses_total_by_status_total` | Nombre total de réponses par code HTTP (200, 404, 500...) |
| `django_http_requests_latency_including_middlewares_seconds` | Latence des requêtes (histogram) |
| `django_http_requests_before_middlewares_total` | Requêtes avant les middlewares |
| `django_db_new_connections_total` | Nouvelles connexions DB |
| `django_db_execute_total` | Requêtes SQL exécutées |
| `process_cpu_seconds_total` | CPU utilisé par le process Django |
| `process_resident_memory_bytes` | Mémoire utilisée par le process Django |

### 4.4 Métriques Node Exporter (VM)

| Métrique | Description |
|----------|-------------|
| `node_cpu_seconds_total` | Temps CPU par mode (idle, user, system...) |
| `node_memory_MemTotal_bytes` | RAM totale |
| `node_memory_MemAvailable_bytes` | RAM disponible |
| `node_filesystem_size_bytes` | Taille disque |
| `node_filesystem_avail_bytes` | Espace disque disponible |
| `node_load1` | Load average 1 minute |
| `node_network_receive_bytes_total` | Octets réseau reçus |
| `node_network_transmit_bytes_total` | Octets réseau envoyés |

---

## 5. Grafana — Création de dashboards

### 5.1 Connexion

1. Ouvrir `http://192.168.88.134:3000`
2. Identifiants : `admin` / `Admin123!`
3. Vérifier la datasource : **Connections** → **Data sources** → **Prometheus** → **Test**

### 5.2 Créer un nouveau dashboard

1. Menu gauche → **Dashboards**
2. Bouton **New** → **New Dashboard**
3. Cliquer **Add visualization**

### 5.3 Ajouter un panel

1. Sélectionner la datasource **Prometheus**
2. Cliquer **Code** (en haut à droite de la zone query) pour écrire en PromQL
3. Écrire la requête
4. Cliquer **Run queries**
5. Donner un titre au panel (cliquer sur "Panel Title")
6. Choisir le type de visualisation (Time series, Gauge, Stat...)
7. Cliquer **Apply**

### 5.4 Panels recommandés

#### Panel 1 — Requêtes HTTP par seconde (Time series)

```promql
rate(django_http_requests_total_by_method_total[5m])
```

- Type : **Time series**
- Legend : `{{method}}`
- Titre : **Requêtes HTTP/s**

#### Panel 2 — Réponses par code status (Time series)

```promql
rate(django_http_responses_total_by_status_total[5m])
```

- Type : **Time series**
- Legend : `{{status}}`
- Titre : **Réponses HTTP par status**

#### Panel 3 — Latence moyenne (Time series)

```promql
rate(django_http_requests_latency_including_middlewares_seconds_sum[5m])
/
rate(django_http_requests_latency_including_middlewares_seconds_count[5m])
```

- Type : **Time series**
- Unit : **seconds (s)**
- Titre : **Latence moyenne**

#### Panel 4 — Erreurs 5xx (Stat)

```promql
increase(django_http_responses_total_by_status_total{status=~"5.."}[1h])
```

- Type : **Stat**
- Titre : **Erreurs 5xx (1h)**
- Thresholds : 0=vert, 1=orange, 10=rouge

#### Panel 5 — CPU VM % (Gauge)

```promql
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

- Type : **Gauge**
- Unit : **Percent (0-100)**
- Titre : **CPU VM**
- Thresholds : 0=vert, 70=orange, 90=rouge

#### Panel 6 — RAM VM % (Gauge)

```promql
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100
```

- Type : **Gauge**
- Unit : **Percent (0-100)**
- Titre : **RAM VM**
- Thresholds : 0=vert, 70=orange, 90=rouge

#### Panel 7 — Disque VM % (Gauge)

```promql
(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100
```

- Type : **Gauge**
- Unit : **Percent (0-100)**
- Titre : **Disque VM**
- Thresholds : 0=vert, 70=orange, 90=rouge

#### Panel 8 — Mémoire process Django (Time series)

```promql
process_resident_memory_bytes{job="apm-web"} / 1024 / 1024
```

- Type : **Time series**
- Unit : **megabytes (MB)**
- Titre : **Mémoire Django (MB)**

### 5.5 Disposition recommandée

```
┌────────────────────────────┬────────────────────────────┐
│   Requêtes HTTP/s          │   Réponses par status      │
│   (Time series)            │   (Time series)            │
├────────────────────────────┼────────────────────────────┤
│   Latence moyenne          │   Mémoire Django (MB)      │
│   (Time series)            │   (Time series)            │
├─────────┬──────────────────┼────────────────────────────┤
│ CPU VM  │  RAM VM          │  Disque VM   │ Erreurs 5xx │
│ (Gauge) │  (Gauge)         │  (Gauge)     │ (Stat)      │
└─────────┴──────────────────┴─────────────-┴─────────────┘
```

### 5.6 Sauvegarder le dashboard

- Icône disquette (💾) en haut à droite ou `Ctrl+S`
- Nom : **APM Platform Overview**
- Cliquer **Save**

### 5.7 Configurer le rafraîchissement automatique

- En haut à droite, cliquer sur l'icône d'horloge
- Choisir **Auto-refresh** : `10s`, `30s` ou `1m`

---

## 6. Sécurité du monitoring

### 6.1 Protection de /metrics (Django)

L'endpoint `/metrics` est protégé par `MetricsAccessMiddleware` :

| Accès autorisé si... | Détail |
|----------------------|--------|
| IP privée / loopback | Prometheus dans le même réseau Docker passe automatiquement |
| Token `X-Metrics-Token` | Header HTTP avec la valeur de `METRICS_TOKEN` |
| Admin DSI authentifié | Session Django active avec rôle Admin DSI |

Si besoin d'ajouter le token dans Prometheus, modifier `docker/prometheus/prometheus.yml` :

```yaml
  - job_name: apm-web
    metrics_path: /metrics
    static_configs:
      - targets: ["web:8000"]
    authorization:
      type: "X-Metrics-Token"
      credentials: "mon-token-prometheus-secret"
```

### 6.2 Protection de Grafana

- Changer le mot de passe par défaut dans `.env` (`GRAFANA_ADMIN_PASSWORD`)
- En production, ne pas exposer le port 3000 publiquement (accès VPN ou réseau interne uniquement)

### 6.3 Protection de Prometheus

- En production, ne pas exposer le port 9090 publiquement
- Prometheus n'a pas d'authentification native — utiliser un reverse proxy ou un réseau privé

---

## 7. Dépannage

| Problème | Cause probable | Solution |
|----------|---------------|----------|
| Prometheus ne démarre pas (`Restarting`) | Erreur YAML dans `prometheus.yml` | `sudo docker compose logs prometheus` pour voir l'erreur |
| Target `apm-web` DOWN | `/metrics` bloqué par le middleware | Vérifier que Prometheus est dans le réseau Docker |
| Target `node` DOWN | Node Exporter pas installé ou port 9100 bloqué | Installer node_exporter et vérifier `curl localhost:9100/metrics` |
| Grafana "No data" | Pas de trafic sur l'app ou mauvaise plage de temps | Naviguer sur l'app, changer le time range à "Last 15 minutes" |
| Grafana datasource en erreur | Mauvaise URL Prometheus | Utiliser `http://prometheus:9090` (réseau Docker) |
| Prometheus "UNKNOWN" pour lui-même | Normal au premier scrape | Attendre 15-30 secondes |

---

## 8. Commandes utiles

```bash
# Démarrer Prometheus + Grafana
sudo docker compose --profile observability up -d

# Arrêter Prometheus + Grafana
sudo docker compose --profile observability down

# Redémarrer Prometheus (après modif de config)
sudo docker compose --profile observability restart prometheus

# Voir les logs
sudo docker compose logs prometheus --tail=30
sudo docker compose logs grafana --tail=30

# Vérifier que /metrics Django répond
curl -s http://localhost:8000/metrics | head -10

# Vérifier que Node Exporter répond
curl -s http://localhost:9100/metrics | head -10

# Tester la datasource Prometheus depuis Grafana
# Connections → Data sources → Prometheus → Test
```

---

## 9. Fichiers du projet liés au monitoring

| Fichier | Rôle |
|---------|------|
| `docker-compose.yml` | Services Prometheus et Grafana (profil `observability`) |
| `docker/prometheus/prometheus.yml` | Configuration de scrape Prometheus |
| `docker/grafana/provisioning/datasources/datasource.yml` | Auto-provisioning de la datasource |
| `docker/grafana/provisioning/dashboards/dashboards.yml` | Auto-provisioning des dashboards (vide) |
| `config/settings/base.py` | `django_prometheus` dans INSTALLED_APPS et MIDDLEWARE |
| `config/urls.py` | `include("django_prometheus.urls")` expose `/metrics` |
| `apps/core/middleware.py` | `MetricsAccessMiddleware` protège `/metrics` |
| `.env` | Variables PROMETHEUS_PORT, GRAFANA_*, METRICS_TOKEN |
