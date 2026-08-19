#!/usr/bin/env python3
"""
APM VM Agent — collecte CPU/RAM/disque et envoie les métriques à l'API.
Renouvelle automatiquement le token JWT via le refresh token.
"""
from __future__ import annotations

import configparser
import os
import socket
import sys
import time
from pathlib import Path

import psutil
import requests

DEFAULT_CONFIG = Path("/opt/apm-agent/config.ini")
LOCAL_CONFIG = Path(__file__).resolve().parent / "config.ini"

access_token: str | None = None
token_expires_at: float = 0


def load_config() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    path = Path(os.environ.get("APM_AGENT_CONFIG", DEFAULT_CONFIG if DEFAULT_CONFIG.exists() else LOCAL_CONFIG))
    if not path.exists():
        print(f"[ERR] Fichier config introuvable: {path}", file=sys.stderr)
        sys.exit(1)
    cfg.read(path)
    return cfg


def cfg_get(cfg: configparser.ConfigParser, section: str, key: str, fallback: str = "") -> str:
    if cfg.has_option(section, key):
        return cfg.get(section, key).strip()
    return fallback


def obtain_tokens(cfg: configparser.ConfigParser) -> tuple[str, str]:
    base = cfg_get(cfg, "api", "base_url").rstrip("/")
    username = cfg_get(cfg, "auth", "username")
    password = cfg_get(cfg, "auth", "password")
    resp = requests.post(
        f"{base}/api/auth/token/",
        json={"username": username, "password": password},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["access"], data["refresh"]


def refresh_access_token(cfg: configparser.ConfigParser, refresh: str) -> str:
    base = cfg_get(cfg, "api", "base_url").rstrip("/")
    resp = requests.post(
        f"{base}/api/auth/token/refresh/",
        json={"refresh": refresh},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access"]


def get_access_token(cfg: configparser.ConfigParser) -> str:
    global access_token, token_expires_at

    now = time.time()
    if access_token and now < token_expires_at - 60:
        return access_token

    static = cfg_get(cfg, "auth", "access_token")
    if static and now < token_expires_at - 60 and access_token:
        return access_token

    refresh = cfg_get(cfg, "auth", "refresh_token")
    if refresh:
        access_token = refresh_access_token(cfg, refresh)
        token_expires_at = now + 50 * 60
        print("[OK] Token JWT renouvelé")
        return access_token

    access, refresh_stored = obtain_tokens(cfg)
    access_token = access
    token_expires_at = now + 50 * 60
    if refresh_stored:
        print("[INFO] Utilisez refresh_token dans config.ini pour renouvellement auto")
    return access_token


def collect_metrics() -> dict:
    return {
        "hostname": socket.gethostname(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_total": psutil.virtual_memory().total,
        "memory_used": psutil.virtual_memory().used,
        "memory_percent": psutil.virtual_memory().percent,
        "disk_total": psutil.disk_usage("/").total,
        "disk_used": psutil.disk_usage("/").used,
        "disk_percent": psutil.disk_usage("/").percent,
        "net_bytes_sent": psutil.net_io_counters().bytes_sent,
        "net_bytes_recv": psutil.net_io_counters().bytes_recv,
        "load_avg_1": psutil.getloadavg()[0] if hasattr(psutil, "getloadavg") else 0,
        "uptime_seconds": time.time() - psutil.boot_time(),
    }


def main() -> None:
    cfg = load_config()
    base = cfg_get(cfg, "api", "base_url").rstrip("/")
    metrics_url = cfg_get(cfg, "api", "metrics_url") or f"{base}/api/servers/metrics/"
    interval = cfg.getint("agent", "interval_seconds", fallback=5)

    print(f"[INFO] Agent démarré → {metrics_url} (intervalle {interval}s)")

    while True:
        try:
            token = get_access_token(cfg)
            resp = requests.post(
                metrics_url,
                json=collect_metrics(),
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            print(f"[OK] {resp.status_code}")
            if resp.status_code == 401:
                access_token = None
                token_expires_at = 0
        except Exception as exc:
            print(f"[ERR] {exc}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
