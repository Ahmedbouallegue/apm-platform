"""
Charge la base APM avec des données de démonstration Topnet DSI.

Usage:
  python manage.py seed_demo_data
  python manage.py seed_demo_data --force
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.applications.models import Application
from apps.audit.services.audit import audit_log_create
from apps.certificates.models import Certificate
from apps.contracts.models import Contract
from apps.dependencies.models import Dependency
from apps.documents.models import Document, Tag
from apps.domains.models import Domain
from apps.environments.models import Environment
from apps.incidents.models import Incident
from apps.notifications.models import Notification
from apps.servers.models import Server
from apps.technologies.models import Technology
from apps.vendors.models import Vendor

User = get_user_model()


class Command(BaseCommand):
    help = "Peuple la base avec un jeu de données de démonstration APM Topnet"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Réinjecte même si des applications existent déjà",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if Application.objects.exists() and not options["force"]:
            self.stdout.write(
                self.style.WARNING(
                    "Des données existent déjà. Relancez avec --force pour réinjecter."
                )
            )
            return

        today = timezone.localdate()
        now = timezone.now()

        users = self._seed_users()
        techs = self._seed_technologies()
        servers = self._seed_servers()
        apps = self._seed_applications(users, techs)
        envs = self._seed_environments(apps, servers)
        domains = self._seed_domains(apps, envs)
        self._seed_certificates(apps, envs, domains, today)
        vendors = self._seed_vendors()
        self._seed_contracts(vendors, apps, users, today)
        self._seed_documents(apps, users)
        self._seed_incidents(apps, users, now)
        self._seed_dependencies(apps)
        self._seed_notifications(users, now)
        self._seed_audit(users)

        self.stdout.write(self.style.SUCCESS("Base de données peuplée avec succès."))
        self.stdout.write("Comptes de démo :")
        self.stdout.write("  admin / Admin123!")
        self.stdout.write("  dsi / Dsi12345!")
        self.stdout.write("  manager / Manager123!")
        self.stdout.write("  viewer / Viewer123!")

    def _seed_users(self):
        specs = [
            ("admin", "admin@topnet.tn", "Admin", "Topnet", User.Role.ADMIN, "Admin123!", True),
            ("dsi", "dsi@topnet.tn", "Sami", "Ben Salah", User.Role.DSI, "Dsi12345!", True),
            ("manager", "manager@topnet.tn", "Achref", "Khelifi", User.Role.MANAGER, "Manager123!", False),
            ("viewer", "viewer@topnet.tn", "Ines", "Trabelsi", User.Role.VIEWER, "Viewer123!", False),
        ]
        users = {}
        for username, email, first, last, role, password, staff in specs:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first,
                    "last_name": last,
                    "role": role,
                    "department": "DSI",
                    "phone": "+216 71 000 000",
                    "is_staff": staff or role == User.Role.ADMIN,
                    "is_active": True,
                },
            )
            if created:
                user.set_password(password)
                user.save()
            else:
                # Keep role/staff flags coherent on re-seed (esp. Lecteur).
                changed = []
                if user.role != role:
                    user.role = role
                    changed.append("role")
                want_staff = bool(staff or role == User.Role.ADMIN)
                if user.is_staff != want_staff:
                    user.is_staff = want_staff
                    changed.append("is_staff")
                if role == User.Role.VIEWER and user.is_superuser:
                    user.is_superuser = False
                    changed.append("is_superuser")
                if changed:
                    user.save(update_fields=changed)
            users[username] = user
        return users

    def _seed_technologies(self):
        items = [
            ("Python", Technology.TechType.LANGUAGE, "3.12"),
            ("Django", Technology.TechType.FRAMEWORK, "5.1"),
            ("PostgreSQL", Technology.TechType.DATABASE, "16"),
            ("Redis", Technology.TechType.MIDDLEWARE, "7"),
            ("React", Technology.TechType.FRAMEWORK, "18"),
            ("Java", Technology.TechType.LANGUAGE, "17"),
            ("Spring Boot", Technology.TechType.FRAMEWORK, "3.2"),
            ("Oracle", Technology.TechType.DATABASE, "19c"),
            ("Docker", Technology.TechType.TOOL, "24"),
            ("Kubernetes", Technology.TechType.CLOUD, "1.29"),
            ("Nginx", Technology.TechType.MIDDLEWARE, "1.25"),
            ("Active Directory", Technology.TechType.OTHER, ""),
        ]
        techs = {}
        for name, tech_type, version in items:
            tech, _ = Technology.objects.get_or_create(
                name=name,
                version=version,
                defaults={"tech_type": tech_type, "description": f"{name} {version}".strip()},
            )
            techs[name] = tech
        return techs

    def _seed_servers(self):
        items = [
            ("srv-app-01", "10.20.1.10", Server.ServerType.VM, "DC Tunis", "Ubuntu 22.04", "8 vCPU", "32 Go"),
            ("srv-app-02", "10.20.1.11", Server.ServerType.VM, "DC Tunis", "Ubuntu 22.04", "16 vCPU", "64 Go"),
            ("srv-db-01", "10.20.2.10", Server.ServerType.PHYSICAL, "DC Tunis", "RHEL 9", "32 CPU", "128 Go"),
            ("srv-web-cloud", "10.30.1.5", Server.ServerType.CLOUD, "Azure North Africa", "Ubuntu 22.04", "4 vCPU", "16 Go"),
        ]
        servers = {}
        for name, ip, stype, dc, os_name, cpu, ram in items:
            srv, _ = Server.objects.get_or_create(
                name=name,
                defaults={
                    "ip_address": ip,
                    "server_type": stype,
                    "datacenter": dc,
                    "os": os_name,
                    "cpu": cpu,
                    "ram": ram,
                    "is_active": True,
                    "notes": "Serveur de démonstration",
                },
            )
            servers[name] = srv
        return servers

    def _seed_applications(self, users, techs):
        specs = [
            {
                "name": "Portail RH",
                "description": "Portail intranet RH Topnet (congés, paie, collab).",
                "criticality": Application.Criticality.CRITICAL,
                "status": Application.Status.PRODUCTION,
                "business_unit": "Ressources Humaines",
                "user_count": 1200,
                "owner": users["dsi"],
                "techs": ["Python", "Django", "PostgreSQL", "Redis"],
            },
            {
                "name": "API Paie",
                "description": "API de calcul et restitution des bulletins de paie.",
                "criticality": Application.Criticality.HIGH,
                "status": Application.Status.PRODUCTION,
                "business_unit": "Finance",
                "user_count": 80,
                "owner": users["manager"],
                "techs": ["Java", "Spring Boot", "Oracle"],
            },
            {
                "name": "CRM Commercial",
                "description": "Gestion de la relation client et du pipeline commercial.",
                "criticality": Application.Criticality.HIGH,
                "status": Application.Status.PRODUCTION,
                "business_unit": "Commercial",
                "user_count": 350,
                "owner": users["manager"],
                "techs": ["React", "Django", "PostgreSQL"],
            },
            {
                "name": "Billing",
                "description": "Facturation abonnés et rapprochement bancaire.",
                "criticality": Application.Criticality.CRITICAL,
                "status": Application.Status.MAINTENANCE,
                "business_unit": "Finance",
                "user_count": 60,
                "owner": users["dsi"],
                "techs": ["Java", "Oracle", "Nginx"],
            },
            {
                "name": "Selfcare Abonnés",
                "description": "Espace client web et mobile Topnet.",
                "criticality": Application.Criticality.MEDIUM,
                "status": Application.Status.PROJECT,
                "business_unit": "Marketing Digital",
                "user_count": 0,
                "owner": users["manager"],
                "techs": ["React", "Python", "PostgreSQL", "Docker"],
            },
        ]
        apps = {}
        for spec in specs:
            app, created = Application.objects.get_or_create(
                name=spec["name"],
                defaults={
                    "description": spec["description"],
                    "criticality": spec["criticality"],
                    "status": spec["status"],
                    "business_unit": spec["business_unit"],
                    "user_count": spec["user_count"],
                    "owner": spec["owner"],
                    "go_live_date": date(2023, 3, 15)
                    if spec["status"] == Application.Status.PRODUCTION
                    else None,
                },
            )
            if created or not app.technologies.exists():
                app.technologies.set([techs[n] for n in spec["techs"] if n in techs])
            apps[spec["name"]] = app
        return apps

    def _seed_environments(self, apps, servers):
        mapping = [
            ("Portail RH", Environment.EnvType.PROD, "https://rh.topnet.tn", "srv-app-02", True, True),
            ("Portail RH", Environment.EnvType.RECETTE, "https://rh-rec.topnet.tn", "srv-app-01", True, False),
            ("API Paie", Environment.EnvType.PROD, "https://api-paie.topnet.tn", "srv-app-02", True, False),
            ("API Paie", Environment.EnvType.DEV, "https://api-paie-dev.topnet.tn", "srv-app-01", True, False),
            ("CRM Commercial", Environment.EnvType.PROD, "https://crm.topnet.tn", "srv-web-cloud", True, True),
            ("Billing", Environment.EnvType.PROD, "https://billing.topnet.tn", "srv-db-01", False, False),
            ("Selfcare Abonnés", Environment.EnvType.DEV, "https://selfcare-dev.topnet.tn", "srv-web-cloud", True, True),
        ]
        envs = {}
        for app_name, env_type, url, server_name, docker, k8s in mapping:
            env, _ = Environment.objects.get_or_create(
                application=apps[app_name],
                env_type=env_type,
                defaults={
                    "name": f"{app_name} {env_type.upper()}",
                    "url": url,
                    "server": servers[server_name],
                    "os": servers[server_name].os,
                    "cpu": servers[server_name].cpu,
                    "ram": servers[server_name].ram,
                    "hosting_provider": "Topnet DC" if "cloud" not in server_name else "Azure",
                    "docker": docker,
                    "kubernetes": k8s,
                    "is_active": True,
                    "ip_address": servers[server_name].ip_address,
                },
            )
            envs[f"{app_name}:{env_type}"] = env
        return envs

    def _seed_domains(self, apps, envs):
        items = [
            ("rh.topnet.tn", "Portail RH", "prod", True, 200),
            ("crm.topnet.tn", "CRM Commercial", "prod", True, 120),
            ("billing.topnet.tn", "Billing", "prod", True, 40),
            ("api-paie.topnet.tn", "API Paie", "prod", False, 90),
            ("selfcare.topnet.tn", "Selfcare Abonnés", None, True, 25),
        ]
        domains = {}
        for fqdn, app_name, env_type, primary, days in items:
            env = envs.get(f"{app_name}:{env_type}") if env_type else None
            domain, _ = Domain.objects.get_or_create(
                fqdn=fqdn,
                defaults={
                    "registrar": "ATI / OVH",
                    "dns_provider": "Cloudflare",
                    "registered_at": date(2022, 1, 10),
                    "expires_at": date.today() + timedelta(days=days),
                    "status": Domain.Status.EXPIRING if days < 60 else Domain.Status.ACTIVE,
                    "application": apps[app_name],
                    "environment": env,
                    "is_primary": primary,
                    "is_active": True,
                    "notes": "Domaine de démonstration",
                },
            )
            domains[fqdn] = domain
        return domains

    def _seed_certificates(self, apps, envs, domains, today):
        items = [
            ("*.topnet.tn", "wildcard", 45, "Portail RH", "prod", "rh.topnet.tn"),
            ("crm.topnet.tn", "single", 20, "CRM Commercial", "prod", "crm.topnet.tn"),
            ("billing.topnet.tn", "single", 120, "Billing", "prod", "billing.topnet.tn"),
            ("api-paie.topnet.tn", "single", 15, "API Paie", "prod", "api-paie.topnet.tn"),
        ]
        for cn, ctype, days, app_name, env_type, fqdn in items:
            Certificate.objects.get_or_create(
                common_name=cn,
                defaults={
                    "san_domains": fqdn,
                    "issuer": "Let's Encrypt",
                    "certificate_type": ctype,
                    "status": Certificate.Status.EXPIRING if days <= 45 else Certificate.Status.VALID,
                    "application": apps[app_name],
                    "environment": envs.get(f"{app_name}:{env_type}"),
                    "domain": domains.get(fqdn),
                    "issued_at": today - timedelta(days=300),
                    "expires_at": today + timedelta(days=days),
                    "auto_renew": True,
                    "is_active": True,
                },
            )

    def _seed_vendors(self):
        items = [
            ("Orange Business", Vendor.VendorType.TELECOM, "support@orange.tn"),
            ("Microsoft", Vendor.VendorType.SOFTWARE, "partners@microsoft.com"),
            ("IBM Support", Vendor.VendorType.MAINTENANCE, "support@ibm.com"),
            ("DigiCert", Vendor.VendorType.SECURITY, "orders@digicert.com"),
            ("OVHcloud", Vendor.VendorType.HOSTING, "support@ovh.com"),
        ]
        vendors = {}
        for name, vtype, email in items:
            vendor, _ = Vendor.objects.get_or_create(
                name=name,
                defaults={
                    "vendor_type": vtype,
                    "contact_name": "Service Support",
                    "contact_email": email,
                    "contact_phone": "+216 71 111 000",
                    "website": f"https://www.{name.split()[0].lower()}.com",
                    "is_active": True,
                },
            )
            vendors[name] = vendor
        return vendors

    def _seed_contracts(self, vendors, apps, users, today):
        items = [
            ("CTR-2025-001", "Maintenance Portail RH", "IBM Support", "Portail RH", Contract.ContractType.MAINTENANCE, 180, "24000.000"),
            ("CTR-2025-014", "Licences M365", "Microsoft", "CRM Commercial", Contract.ContractType.LICENSE, 40, "56000.000"),
            ("CTR-2024-088", "Support Billing 24/7", "Orange Business", "Billing", Contract.ContractType.SUPPORT, 25, "18000.000"),
            ("CTR-2025-033", "Hébergement Azure", "OVHcloud", "Selfcare Abonnés", Contract.ContractType.HOSTING, 200, "9000.000"),
        ]
        for ref, title, vendor_name, app_name, ctype, days, cost in items:
            Contract.objects.get_or_create(
                reference=ref,
                defaults={
                    "title": title,
                    "vendor": vendors[vendor_name],
                    "application": apps[app_name],
                    "contract_type": ctype,
                    "status": Contract.Status.EXPIRING if days < 60 else Contract.Status.ACTIVE,
                    "start_date": today - timedelta(days=300),
                    "end_date": today + timedelta(days=days),
                    "annual_cost": Decimal(cost),
                    "currency": "TND",
                    "auto_renew": False,
                    "sla_level": "24/7",
                    "owner": users["dsi"],
                    "is_active": True,
                    "notes": "Contrat de démonstration",
                },
            )

    def _seed_documents(self, apps, users):
        tags = {}
        for name in ["architecture", "production", "securite", "exploitation", "rh"]:
            tag, _ = Tag.objects.get_or_create(name=name)
            tags[name] = tag

        items = [
            ("Architecture Portail RH.pdf", Document.Category.ARCHITECTURE, "Portail RH", ["architecture", "rh"]),
            ("Manuel utilisateur CRM.docx", Document.Category.USER_MANUAL, "CRM Commercial", ["production"]),
            ("Procédure incident Billing.pdf", Document.Category.PROCEDURE, "Billing", ["exploitation", "securite"]),
            ("Manuel exploitation API Paie.pdf", Document.Category.OPS_MANUAL, "API Paie", ["exploitation"]),
        ]
        for title, category, app_name, tag_names in items:
            doc, created = Document.objects.get_or_create(
                title=title,
                defaults={
                    "file_type": title.split(".")[-1],
                    "category": category,
                    "description": f"Document de démonstration — {title}",
                    "application": apps[app_name],
                    "uploaded_by": users["manager"],
                    "is_active": True,
                },
            )
            if created:
                doc.tags.set([tags[n] for n in tag_names])

    def _seed_incidents(self, apps, users, now):
        Incident.objects.get_or_create(
            title="Indisponibilité CRM Commercial",
            defaults={
                "description": "Timeouts répétés sur l'API CRM pendant 45 minutes.",
                "occurred_at": now - timedelta(days=3),
                "impact": Incident.Impact.MAJOR,
                "root_cause": "Saturation du pool de connexions PostgreSQL.",
                "solution": "Augmentation du pool + redémarrage contrôlé.",
                "status": Incident.Status.RESOLVED,
                "application": apps["CRM Commercial"],
                "reported_by": users["manager"],
            },
        )
        Incident.objects.get_or_create(
            title="Échec batch Billing nocturne",
            defaults={
                "description": "Le job de facturation n'a pas produit les fichiers SEPA.",
                "occurred_at": now - timedelta(hours=18),
                "impact": Incident.Impact.CRITICAL,
                "root_cause": "",
                "solution": "",
                "status": Incident.Status.IN_PROGRESS,
                "application": apps["Billing"],
                "reported_by": users["dsi"],
            },
        )
        Incident.objects.get_or_create(
            title="Latence Portail RH",
            defaults={
                "description": "Temps de réponse > 4s sur l'écran congés.",
                "occurred_at": now - timedelta(days=10),
                "impact": Incident.Impact.MINOR,
                "root_cause": "Requête N+1 sur le module absences.",
                "solution": "Optimisation ORM + cache Redis.",
                "status": Incident.Status.CLOSED,
                "application": apps["Portail RH"],
                "reported_by": users["viewer"],
            },
        )

    def _seed_dependencies(self, apps):
        Dependency.objects.get_or_create(
            source_application=apps["Portail RH"],
            target_application=apps["API Paie"],
            defaults={
                "dependency_type": Dependency.DependencyType.API,
                "description": "Consultation des bulletins de paie",
                "is_active": True,
            },
        )
        Dependency.objects.get_or_create(
            source_application=apps["Portail RH"],
            target_external="Active Directory",
            defaults={
                "dependency_type": Dependency.DependencyType.AUTH,
                "description": "SSO collaborateurs Topnet",
                "is_active": True,
            },
        )
        Dependency.objects.get_or_create(
            source_application=apps["CRM Commercial"],
            target_application=apps["Billing"],
            defaults={
                "dependency_type": Dependency.DependencyType.API,
                "description": "Création des commandes facturables",
                "is_active": True,
            },
        )
        Dependency.objects.get_or_create(
            source_application=apps["Billing"],
            target_external="PostgreSQL / Oracle Finance",
            defaults={
                "dependency_type": Dependency.DependencyType.DATABASE,
                "description": "Stockage des écritures de facturation",
                "is_active": True,
            },
        )

    def _seed_notifications(self, users, now):
        for user in users.values():
            Notification.objects.get_or_create(
                user=user,
                title="Bienvenue sur Topnet APM",
                defaults={
                    "message": "La plateforme de gestion du patrimoine applicatif est prête.",
                    "notification_type": Notification.NotificationType.INFO,
                    "status": Notification.Status.UNREAD,
                    "link": "/",
                },
            )
        Notification.objects.get_or_create(
            user=users["dsi"],
            title="Certificat SSL bientôt expiré — crm.topnet.tn",
            defaults={
                "message": "Le certificat expire dans moins de 30 jours.",
                "notification_type": Notification.NotificationType.EXPIRY,
                "status": Notification.Status.UNREAD,
                "link": "/certificates/",
            },
        )
        Notification.objects.get_or_create(
            user=users["manager"],
            title="Incident ouvert — Billing",
            defaults={
                "message": "Échec batch nocturne en cours d'analyse.",
                "notification_type": Notification.NotificationType.INCIDENT,
                "status": Notification.Status.UNREAD,
                "link": "/incidents/",
            },
        )

    def _seed_audit(self, users):
        audit_log_create(
            action="seed",
            entity="System",
            entity_id="demo",
            details="Chargement du jeu de données de démonstration APM",
            user=users["admin"],
        )
        audit_log_create(
            action="create",
            entity="Application",
            entity_id="Portail RH",
            details="Application de démonstration créée",
            user=users["dsi"],
        )
