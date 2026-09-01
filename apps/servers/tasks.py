from celery import shared_task


@shared_task
def ping() -> str:
    """Celery connectivity check for this app."""
    return "pong"


def ping_host(ip: str) -> bool:
    """Pings a host and returns True if it's reachable."""
    import logging
    import platform
    import subprocess
    logger = logging.getLogger(__name__)

    param = '-n' if platform.system().lower() == 'windows' else '-c'
    timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
    timeout_val = '2000' if platform.system().lower() == 'windows' else '2'
    
    command = ['ping', param, '1', timeout_param, timeout_val, ip]
    
    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT, timeout=3)
        return True
    except subprocess.CalledProcessError:
        return False
    except subprocess.TimeoutExpired:
        return False
    except Exception as exc:
        logger.warning("Erreur ping vers %s: %s", ip, exc)
        return False


@shared_task(name="apps.servers.tasks.ping_all_servers")
def ping_all_servers():
    """Pings all active servers and updates their ping_status."""
    import logging
    from concurrent.futures import ThreadPoolExecutor

    from django.utils import timezone

    from apps.servers.models import Server
    
    logger = logging.getLogger(__name__)
    servers = list(Server.objects.filter(is_active=True, is_deleted=False))
    if not servers:
        return "No servers to ping"
    
    logger.info("Démarrage du ping de %d serveurs...", len(servers))
    now = timezone.now()
    
    def process_server(server):
        is_up = ping_host(server.ip_address)
        new_status = Server.PingStatus.UP if is_up else Server.PingStatus.DOWN
        
        # Simple logging for now
        if server.ping_status == Server.PingStatus.UP and new_status == Server.PingStatus.DOWN:
            logger.warning("Serveur %s (%s) est passé HORS LIGNE !", server.name, server.ip_address)
            
        server.ping_status = new_status
        server.last_ping_at = now
        return server

    with ThreadPoolExecutor(max_workers=10) as executor:
        updated_servers = list(executor.map(process_server, servers))
        
    Server.objects.bulk_update(updated_servers, ["ping_status", "last_ping_at"])
    
    up_count = sum(1 for s in updated_servers if s.ping_status == Server.PingStatus.UP)
    return f"Pinged {len(servers)} servers. {up_count} UP."
