# Guide de déploiement — Agent de monitoring VM

## Architecture

```
┌─────────────────┐        POST /api/servers/metrics/        ┌─────────────────────┐
│   VM Agent       │ ──────────────────────────────────────▶  │   APM Platform       │
│  (Python script) │        toutes les 60 secondes           │   (Django + Docker)  │
│  sur chaque VM   │                                         │   sur la VM serveur  │
└─────────────────┘                                         └─────────────────────┘
                                                                     │
                                                              Page Monitoring
                                                            /servers/<id>/monitoring/
                                                            (graphiques CPU/RAM/Disque)
```

---

## Partie 1 — Windows (développement du code Django)

### Étape 1.1 : Modèle ServerMetric

Fichier modifié : `apps/servers/models.py`

Un nouveau modèle `ServerMetric` a été ajouté avec les champs :
- `server` (ForeignKey vers Server)
- `hostname`, `cpu_percent`, `memory_total`, `memory_used`, `memory_percent`
- `disk_total`, `disk_used`, `disk_percent`
- `net_bytes_sent`, `net_bytes_recv`, `load_avg_1`, `uptime_seconds`
- `collected_at` (auto, date/heure de collecte)

### Étape 1.2 : Migration

```bash
python manage.py makemigrations servers --name add_servermetric
```

Fichier créé : `apps/servers/migrations/0002_add_servermetric.py`

### Étape 1.3 : Serializer

Fichier créé : `apps/servers/serializers/metrics.py`

Deux serializers :
- `ServerMetricWriteSerializer` — valide les données envoyées par l'agent. Fait la correspondance hostname → serveur en base (par nom ou par IP).
- `ServerMetricReadSerializer` — sérialise les métriques pour l'API GET.

### Étape 1.4 : Vues API

Fichier modifié : `apps/servers/views/api.py`

Deux nouvelles vues :
- `ServerMetricIngestView` — `POST /api/servers/metrics/` : reçoit les métriques de l'agent.
- `ServerMetricListView` — `GET /api/servers/metrics/list/?server_id=X&hours=24` : retourne les métriques pour un serveur.

### Étape 1.5 : URLs API

Fichier modifié : `apps/servers/urls.py`

Ajout de :
```
POST /api/servers/metrics/        → réception des métriques
GET  /api/servers/metrics/list/   → lecture des métriques
```

### Étape 1.6 : Vue web Monitoring

Fichier modifié : `apps/servers/views/web.py`

Nouvelle vue `ServerMonitoringView` accessible sur `/servers/<id>/monitoring/`.
- En mode normal : affiche le template HTML avec les graphiques.
- En mode AJAX (`X-Requested-With: XMLHttpRequest`) : retourne les métriques en JSON pour rafraîchir les graphiques.

### Étape 1.7 : URL web

Fichier modifié : `apps/servers/urls_web.py`

Ajout de :
```
/servers/<id>/monitoring/  → page de monitoring
```

### Étape 1.8 : Template Monitoring

Fichier créé : `templates/servers/monitoring.html`

Contient :
- 5 indicateurs en temps réel (CPU, RAM, Disque, Load, Uptime)
- 4 graphiques Chart.js (CPU, RAM, Disque, Réseau)
- Sélecteur de plage horaire (1h, 6h, 24h, 3j, 7j)
- Rafraîchissement automatique toutes les 30 secondes
- Code couleur : vert (<70%), orange (70-90%), rouge (>90%)

### Étape 1.9 : Bouton Monitoring sur la fiche serveur

Fichier modifié : `templates/servers/detail.html`

Ajout d'un bouton "Monitoring" dans les actions de la fiche serveur.

### Étape 1.10 : Admin Django

Fichier modifié : `apps/servers/admin.py`

Enregistrement du modèle `ServerMetric` dans l'admin Django.

---

## Partie 2 — Linux / VM (déploiement et agent)

### Étape 2.1 : Transférer le code sur la VM

Option A — Git :
```bash
cd ~/Desktop/apm-platform
git pull origin main
```

Option B — Copie manuelle (SCP depuis Windows) :
```bash
scp -r C:\Users\clash\apm-platform\* ahmed@192.168.88.134:~/Desktop/apm-platform/
```

### Étape 2.2 : Rebuild et migration

```bash
cd ~/Desktop/apm-platform
sudo docker compose up -d --build
sudo docker compose exec web python manage.py migrate
sudo docker compose exec web python manage.py collectstatic --noinput
```

Vérifier que la migration est bien passée :
```bash
sudo docker compose exec web python manage.py showmigrations servers
```

Résultat attendu :
```
servers
 [X] 0001_initial
 [X] 0002_add_servermetric
```

### Étape 2.3 : Créer un serveur dans l'application

1. Ouvrir `http://192.168.88.134/servers/new/`
2. Remplir :
   - **Nom** : le hostname de la VM (vérifier avec `hostname` dans le terminal)
   - **IP** : `192.168.88.134`
   - **Type** : VM
3. Sauvegarder

> **Important** : le nom du serveur doit correspondre **exactement** au hostname retourné par la commande `hostname` sur la VM.

### Étape 2.4 : Obtenir un token JWT

```bash
curl -X POST http://192.168.88.134/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123!"}'
```

Copier la valeur du champ `access` dans la réponse.

> **Note** : le token access expire au bout d'1 heure. Pour une utilisation en production, il faudrait implémenter le renouvellement automatique avec le refresh token.

### Étape 2.5 : Installer les dépendances de l'agent

```bash
sudo apt install python3-pip -y
sudo pip3 install psutil requests
```

### Étape 2.6 : Créer le script agent

```bash
sudo mkdir -p /opt/apm-agent
sudo nano /opt/apm-agent/agent.py
```

Coller le contenu suivant :

```python
import psutil
import requests
import socket
import time

API_URL = "http://192.168.88.134/api/servers/metrics/"
API_TOKEN = "COLLER_LE_TOKEN_ACCESS_ICI"

def collect_metrics():
    return {
        "hostname": socket.gethostname(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_total": psutil.virtual_memory().total,
        "memory_used": psutil.virtual_memory().used,
        "memory_percent": psutil.virtual_memory().percent,
        "disk_total": psutil.disk_usage('/').total,
        "disk_used": psutil.disk_usage('/').used,
        "disk_percent": psutil.disk_usage('/').percent,
        "net_bytes_sent": psutil.net_io_counters().bytes_sent,
        "net_bytes_recv": psutil.net_io_counters().bytes_recv,
        "load_avg_1": psutil.getloadavg()[0],
        "uptime_seconds": time.time() - psutil.boot_time(),
    }

while True:
    try:
        resp = requests.post(
            API_URL,
            json=collect_metrics(),
            headers={"Authorization": f"Bearer {API_TOKEN}"},
            timeout=10,
        )
        print(f"[OK] {resp.status_code}")
    except Exception as e:
        print(f"[ERR] {e}")
    time.sleep(60)
```

### Étape 2.7 : Tester manuellement

```bash
sudo python3 -u /opt/apm-agent/agent.py
```

Résultat attendu : `[OK] 201` (toutes les 60 secondes).

Si erreur :
| Message | Cause | Solution |
|---------|-------|----------|
| `[OK] 401` | Token expiré | Régénérer le token (étape 2.4) |
| `[OK] 400` | Hostname ne correspond pas | Vérifier le nom du serveur dans l'app |
| `[OK] 500` | Migration non appliquée | Relancer étape 2.2 |
| `[ERR] Connection refused` | App non démarrée | `sudo docker compose up -d` |

Arrêter avec `Ctrl+C` une fois validé.

### Étape 2.8 : Créer le service systemd

```bash
sudo nano /etc/systemd/system/apm-agent.service
```

Coller :

```ini
[Unit]
Description=APM Monitoring Agent
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 -u /opt/apm-agent/agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Étape 2.9 : Démarrer le service

```bash
sudo systemctl daemon-reload
sudo systemctl enable apm-agent
sudo systemctl start apm-agent
```

Vérifier :
```bash
sudo systemctl status apm-agent
sudo journalctl -u apm-agent -f
```

### Étape 2.10 : Voir les graphiques

Ouvrir dans le navigateur :
```
http://192.168.88.134/servers/<ID>/monitoring/
```

Ou depuis la fiche du serveur, cliquer sur le bouton **Monitoring**.

Les graphiques se mettent à jour automatiquement toutes les 30 secondes.

---

## Résumé des fichiers modifiés/créés

### Windows (code Django)

| Fichier | Action |
|---------|--------|
| `apps/servers/models.py` | Modifié — ajout modèle `ServerMetric` |
| `apps/servers/migrations/0002_add_servermetric.py` | Créé — migration |
| `apps/servers/serializers/metrics.py` | Créé — serializers |
| `apps/servers/views/api.py` | Modifié — vues API POST/GET |
| `apps/servers/views/web.py` | Modifié — vue web monitoring |
| `apps/servers/urls.py` | Modifié — URLs API |
| `apps/servers/urls_web.py` | Modifié — URL web monitoring |
| `apps/servers/admin.py` | Modifié — admin ServerMetric |
| `templates/servers/monitoring.html` | Créé — page graphiques |
| `templates/servers/detail.html` | Modifié — bouton Monitoring |

### Linux / VM

| Fichier | Action |
|---------|--------|
| `/opt/apm-agent/agent.py` | Créé — script de collecte |
| `/etc/systemd/system/apm-agent.service` | Créé — service systemd |

---

## Commandes utiles

```bash
# Voir les logs de l'agent
sudo journalctl -u apm-agent -f

# Redémarrer l'agent
sudo systemctl restart apm-agent

# Arrêter l'agent
sudo systemctl stop apm-agent

# Voir les logs Django
sudo docker compose logs web --tail=50

# Régénérer un token JWT
curl -X POST http://192.168.88.134/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123!"}'
```
