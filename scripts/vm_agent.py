#!/usr/bin/env python3
"""
APM Platform — VM Agent
=======================
Agent léger à déployer sur chaque VM Ubuntu/Debian.
Il collecte les métriques système (CPU, RAM, Disque, Réseau) et les
envoie périodiquement à l'application APM Platform via son API REST.

Configuration :
    Modifier les variables dans la section CONFIG ci-dessous,
    ou définir les variables d'environnement correspondantes.

Usage :
    python3 vm_agent.py

Dépendances :
    pip3 install psutil requests
"""

import logging
import os
import socket
import sys
import time

# ---------------------------------------------------------------------------
# CONFIG — à adapter selon votre environnement
# ---------------------------------------------------------------------------

# URL de l'application APM Platform sur Windows
# Exemple : "http://192.168.1.50:8000" ou "http://10.0.0.10:8000"
APM_URL = os.environ.get("APM_URL", "http://localhost:8000")

# Identifiants d'un compte APM (doit avoir accès à l'API)
APM_USERNAME = os.environ.get("APM_USERNAME", "admin")
APM_PASSWORD = os.environ.get("APM_PASSWORD", "admin")

# Hostname de la VM (tel qu'enregistré dans APM sous "Nom du serveur")
# Si vide, utilise le hostname système de la machine
SERVER_HOSTNAME = os.environ.get("SERVER_HOSTNAME", "") or socket.gethostname()

# Intervalle d'envoi des métriques (en secondes)
COLLECT_INTERVAL = int(os.environ.get("COLLECT_INTERVAL", "30"))

# ---------------------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------------------
TOKEN_URL = f"{APM_URL}/api/auth/token/"
METRICS_URL = f"{APM_URL}/api/servers/metrics/"

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("vm_agent")


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _import_deps():
    """Vérifie et importe les dépendances requises."""
    try:
        import psutil  # noqa: F401
        import requests  # noqa: F401
    except ImportError as e:
        log.error(
            "Dépendance manquante : %s\n"
            "Installez-la avec : pip3 install psutil requests",
            e,
        )
        sys.exit(1)


def get_jwt_token(session) -> str:
    """Obtient un token JWT via les credentials configurés."""
    log.info("Authentification sur %s …", TOKEN_URL)
    resp = session.post(
        TOKEN_URL,
        json={"username": APM_USERNAME, "password": APM_PASSWORD},
        timeout=10,
    )
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("access") or data.get("token")
        if token:
            log.info("Authentification réussie.")
            return token
    log.error(
        "Échec authentification (HTTP %s) : %s",
        resp.status_code,
        resp.text[:200],
    )
    raise RuntimeError("Impossible d'obtenir le token JWT.")


def collect_metrics() -> dict:
    """Collecte les métriques système via psutil."""
    import psutil

    cpu = psutil.cpu_percent(interval=1)

    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    net = psutil.net_io_counters()

    # Load average (Linux seulement — retourne 0.0 sur Windows)
    try:
        load_avg_1 = psutil.getloadavg()[0]
    except AttributeError:
        load_avg_1 = 0.0

    uptime_seconds = time.time() - psutil.boot_time()

    return {
        "hostname": SERVER_HOSTNAME,
        "cpu_percent": round(cpu, 2),
        "memory_total": mem.total,
        "memory_used": mem.used,
        "memory_percent": round(mem.percent, 2),
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_percent": round(disk.percent, 2),
        "net_bytes_sent": net.bytes_sent,
        "net_bytes_recv": net.bytes_recv,
        "load_avg_1": round(load_avg_1, 2),
        "uptime_seconds": round(uptime_seconds, 1),
    }


def send_metrics(session, token: str, metrics: dict) -> bool:
    """Envoie les métriques à l'API APM. Retourne False si le token est expiré."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = session.post(METRICS_URL, json=metrics, headers=headers, timeout=10)
        if resp.status_code == 201:
            log.info(
                "Métriques envoyées — CPU %.1f%% | RAM %.1f%% | Disk %.1f%%",
                metrics["cpu_percent"],
                metrics["memory_percent"],
                metrics["disk_percent"],
            )
            return True
        elif resp.status_code in (401, 403):
            log.warning("Token expiré ou invalide (HTTP %s).", resp.status_code)
            return False  # Signale qu'il faut renouveler le token
        else:
            log.error(
                "Erreur API (HTTP %s) : %s", resp.status_code, resp.text[:200]
            )
            return True  # Pas un problème de token, on continue
    except Exception as exc:
        log.warning("Impossible d'envoyer les métriques : %s", exc)
        return True  # Continuer la boucle même si réseau temporairement indisponible


# ---------------------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------------------

def main():
    _import_deps()
    import requests

    log.info("=== APM VM Agent démarré ===")
    log.info("Serveur APM    : %s", APM_URL)
    log.info("Hostname agent : %s", SERVER_HOSTNAME)
    log.info("Intervalle     : %ds", COLLECT_INTERVAL)

    session = requests.Session()
    token = None

    while True:
        try:
            # Obtenir / renouveler le token si nécessaire
            if token is None:
                token = get_jwt_token(session)

            # Collecter et envoyer
            metrics = collect_metrics()
            token_still_valid = send_metrics(session, token, metrics)
            if not token_still_valid:
                log.info("Renouvellement du token …")
                token = None
                continue

        except RuntimeError as e:
            log.error("Erreur fatale : %s — nouvelle tentative dans 60s", e)
            token = None
            time.sleep(60)
            continue
        except KeyboardInterrupt:
            log.info("Agent arrêté par l'utilisateur.")
            break
        except Exception as exc:
            log.exception("Erreur inattendue : %s", exc)

        time.sleep(COLLECT_INTERVAL)


if __name__ == "__main__":
    main()
