"""
Commande de peuplement de données d'entreprise Topnet DSI.
Ajoute de nouvelles applications, serveurs, contrats, certificats,
incidents, dépendances et documents pour enrichir le patrimoine applicatif.

Usage:
  python manage.py add_enterprise_data
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.applications.models import Application
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
    help = "Ajoute un jeu étendu de données d'entreprise réelles pour la DSI Topnet"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("==> Ajout de nouvelles données DSI Topnet..."))

        today = timezone.localdate()
        now = timezone.now()

        # Utilisateurs existants
        admin_user = User.objects.filter(username="admin").first() or User.objects.first()
        achref_user = User.objects.filter(username="achref").first() or admin_user
        ines_user = User.objects.filter(username="ines").first() or admin_user
        system_user = User.objects.filter(username="system").first() or admin_user

        # 1. Technologies
        tech_specs = [
            ("Asterisk VoIP", Technology.TechType.MIDDLEWARE, "Plateforme de téléphonie IP, PBX open source et SIP Trunking"),
            ("Zimbra Suite", Technology.TechType.TOOL, "Messagerie d'entreprise collaborative, webmail et calendrier partagé"),
            ("Node.js", Technology.TechType.LANGUAGE, "Runtime JavaScript asynchrone pour microservices temps réel"),
            ("PHP", Technology.TechType.LANGUAGE, "Langage web orienté objet pour portails et supervision"),
            ("MySQL / MariaDB", Technology.TechType.DATABASE, "Système de gestion de bases de données relationnelles SQL"),
            ("Elasticsearch", Technology.TechType.DATABASE, "Moteur de recherche distribué et d'analyse de logs"),
            ("RabbitMQ", Technology.TechType.MIDDLEWARE, "Message broker pour la gestion asynchrone des files d'attente"),
            ("Linux RHEL", Technology.TechType.OS, "Red Hat Enterprise Linux pour systèmes critiques"),
        ]
        techs = {}
        for name, ttype, desc in tech_specs:
            t, created = Technology.objects.get_or_create(
                name=name,
                defaults={"description": desc, "tech_type": ttype},
            )
            techs[name] = t
            if created:
                self.stdout.write(f"  + Technologie : {name}")

        # Technologies déjà présentes
        for t in Technology.objects.all():
            techs[t.name] = t

        # 2. Fournisseurs (Vendors)
        vendor_specs = [
            ("Cisco Systems", Vendor.VendorType.TELECOM, "Équipements réseau, routeurs core et commutateurs backbone", "support-cisco@topnet.tn", "+216 71 111 222", "San Jose, USA / Tunis"),
            ("Synacor (Zimbra)", Vendor.VendorType.SOFTWARE, "Éditeur de la plateforme de messagerie collaborative Zimbra", "sales@synacor.com", "+1 716 853 1362", "Buffalo, NY, USA"),
            ("Dell Technologies", Vendor.VendorType.MAINTENANCE, "Fournisseur de serveurs physiques PowerEdge et baies SAN", "support-dell@topnet.tn", "+216 71 333 444", "Round Rock, TX / Tunis"),
            ("Fortinet", Vendor.VendorType.SECURITY, "Pare-feu de nouvelle génération FortiGate et sécurité réseau UTM", "support@fortinet.com", "+33 1 41 43 70 00", "Sunnyvale, CA, USA"),
        ]
        vendors = {}
        for name, vtype, desc, email, phone, address in vendor_specs:
            v, created = Vendor.objects.get_or_create(
                name=name,
                defaults={
                    "vendor_type": vtype,
                    "notes": desc,
                    "contact_email": email,
                    "contact_phone": phone,
                    "address": address,
                    "is_active": True,
                },
            )
            vendors[name] = v
            if created:
                self.stdout.write(f"  + Fournisseur : {name}")

        for v in Vendor.objects.all():
            vendors[v.name] = v

        # 3. Serveurs (Servers)
        server_specs = [
            ("srv-voip-01", "192.168.10.45", "Ubuntu 24.04 LTS", "16 vCPU", "32 GB", "Datacenter Charguia", Server.ServerType.VM, Server.PingStatus.UP),
            ("srv-b2b-01", "192.168.10.60", "Debian 12", "8 vCPU", "16 GB", "Datacenter Lac", Server.ServerType.VM, Server.PingStatus.UP),
            ("srv-mail-01", "192.168.20.15", "RHEL 9.2", "32 vCPU", "64 GB", "Datacenter Charguia", Server.ServerType.PHYSICAL, Server.PingStatus.UP),
            ("srv-nms-01", "192.168.10.99", "Ubuntu 22.04 LTS", "8 vCPU", "16 GB", "Datacenter Lac", Server.ServerType.VM, Server.PingStatus.UP),
            ("srv-sec-soc-01", "192.168.30.10", "Debian 12", "24 vCPU", "48 GB", "Datacenter Charguia", Server.ServerType.VM, Server.PingStatus.UP),
        ]
        servers = {}
        for name, ip, os_name, cpu, ram, dc, stype, ping in server_specs:
            s, created = Server.objects.get_or_create(
                name=name,
                defaults={
                    "ip_address": ip,
                    "os": os_name,
                    "cpu": cpu,
                    "ram": ram,
                    "datacenter": dc,
                    "server_type": stype,
                    "ping_status": ping,
                    "last_ping_at": now,
                    "is_active": True,
                },
            )
            servers[name] = s
            if created:
                self.stdout.write(f"  + Serveur : {name} ({ip})")

        for s in Server.objects.all():
            servers[s.name] = s

        # 4. Applications
        app_specs = [
            (
                "Portail Partenaires & Revendeurs",
                "Plateforme B2B d'activation d'abonnements, gestion des commissions revendeurs et validation des commandes grands comptes.",
                Application.Criticality.CRITICAL,
                Application.Status.PRODUCTION,
                480,
                "Direction Commerciale B2B",
                achref_user,
                ["Django", "React", "PostgreSQL", "Redis"],
            ),
            (
                "Plateforme VoIP & Centre d'Appels",
                "Gestionnaire de téléphonie IP Topnet, distribution automatique des appels du 77 77 et passerelle SIP Trunking inter-opérateurs.",
                Application.Criticality.CRITICAL,
                Application.Status.PRODUCTION,
                1450,
                "Direction Relation Client & Support",
                system_user,
                ["Asterisk VoIP", "Python", "RabbitMQ", "Redis"],
            ),
            (
                "Topnet Mail Pro (Zimbra)",
                "Service de messagerie professionnelle, agendas partagés, carnet d'adresses et webmail pour l'ensemble du personnel Topnet.",
                Application.Criticality.HIGH,
                Application.Status.PRODUCTION,
                3800,
                "Direction des Systèmes d'Information",
                ines_user,
                ["Zimbra Suite", "Java", "Nginx", "Linux RHEL"],
            ),
            (
                "Supervision NMS & Cacti",
                "Plateforme de métrologie de trafic, cartographie réseau temps réel et surveillance SNMP des routeurs et DSLAMs Topnet.",
                Application.Criticality.HIGH,
                Application.Status.PRODUCTION,
                95,
                "Direction Réseau & NOC",
                system_user,
                ["PHP", "MySQL / MariaDB"],
            ),
            (
                "Passerelle SMS & OTP",
                "Microservice d'envoi massif de SMS transactionnels, codes de vérification OTP et notifications instantanées de facturation.",
                Application.Criticality.CRITICAL,
                Application.Status.PRODUCTION,
                92000,
                "Direction Digitale & Télécoms",
                achref_user,
                ["Node.js", "RabbitMQ", "Redis", "Docker"],
            ),
            (
                "Plateforme SOC & Détection d'Intrusions",
                "Plateforme d'analyse comportementale, détection des attaques DDoS et corrélation SIEM des flux de sécurité réseau.",
                Application.Criticality.HIGH,
                Application.Status.PRODUCTION,
                45,
                "Direction Sécurité & Conformité",
                admin_user,
                ["Elasticsearch", "Python", "Docker"],
            ),
        ]

        apps = {}
        for name, desc, crit, status, users_cnt, bu, owner, app_tech_names in app_specs:
            app, created = Application.objects.get_or_create(
                name=name,
                defaults={
                    "description": desc,
                    "criticality": crit,
                    "status": status,
                    "user_count": users_cnt,
                    "business_unit": bu,
                    "owner": owner,
                    "go_live_date": today - timedelta(days=365),
                },
            )
            for tech_name in app_tech_names:
                if tech_name in techs:
                    app.technologies.add(techs[tech_name])
            apps[name] = app
            if created:
                self.stdout.write(f"  + Application : {name}")

        for a in Application.objects.all():
            apps[a.name] = a

        # 5. Environnements
        env_specs = [
            ("Portail Partenaires & Revendeurs", "Production B2B", Environment.EnvType.PROD, servers.get("srv-b2b-01"), "https://partenaires.topnet.tn", "192.168.10.60"),
            ("Portail Partenaires & Revendeurs", "Recette B2B", Environment.EnvType.RECETTE, servers.get("srv-b2b-01"), "https://recette-partenaires.topnet.tn", "192.168.10.61"),
            ("Plateforme VoIP & Centre d'Appels", "Production VoIP", Environment.EnvType.PROD, servers.get("srv-voip-01"), "https://voip.topnet.tn", "192.168.10.45"),
            ("Topnet Mail Pro (Zimbra)", "Production Webmail", Environment.EnvType.PROD, servers.get("srv-mail-01"), "https://mail.topnet.tn", "192.168.20.15"),
            ("Supervision NMS & Cacti", "Production NMS", Environment.EnvType.PROD, servers.get("srv-nms-01"), "https://nms.topnet.tn", "192.168.10.99"),
            ("Passerelle SMS & OTP", "Production SMS-GW", Environment.EnvType.PROD, servers.get("srv-b2b-01"), "https://sms-gw.topnet.tn", "192.168.10.62"),
            ("Plateforme SOC & Détection d'Intrusions", "Production SOC", Environment.EnvType.PROD, servers.get("srv-sec-soc-01"), "https://soc.topnet.tn", "192.168.30.10"),
        ]

        envs = {}
        for app_name, env_name, etype, srv, url, ip in env_specs:
            if app_name in apps:
                e, created = Environment.objects.get_or_create(
                    application=apps[app_name],
                    env_type=etype,
                    defaults={
                        "name": env_name,
                        "server": srv,
                        "url": url,
                        "ip_address": ip,
                        "os": srv.os if srv else "",
                        "cpu": srv.cpu if srv else "",
                        "ram": srv.ram if srv else "",
                        "docker": True,
                        "is_active": True,
                    },
                )
                envs[f"{app_name}_{etype}"] = e
                if created:
                    self.stdout.write(f"  + Environnement : {app_name} [{etype}]")

        # 6. Domaines
        domain_specs = [
            ("partenaires.topnet.tn", "ATI / Topnet", apps.get("Portail Partenaires & Revendeurs"), today + timedelta(days=210)),
            ("mail.topnet.tn", "ATI / Topnet", apps.get("Topnet Mail Pro (Zimbra)"), today + timedelta(days=280)),
            ("voip.topnet.tn", "ATI / Topnet", apps.get("Plateforme VoIP & Centre d'Appels"), today + timedelta(days=320)),
            ("sms-gw.topnet.tn", "ATI / Topnet", apps.get("Passerelle SMS & OTP"), today + timedelta(days=150)),
            ("soc.topnet.tn", "ATI / Topnet", apps.get("Plateforme SOC & Détection d'Intrusions"), today + timedelta(days=190)),
        ]

        domains = {}
        for fqdn, registrar, app, exp in domain_specs:
            d, created = Domain.objects.get_or_create(
                fqdn=fqdn,
                defaults={
                    "registrar": registrar,
                    "application": app,
                    "expires_at": exp,
                    "is_active": True,
                },
            )
            domains[fqdn] = d
            if created:
                self.stdout.write(f"  + Domaine : {fqdn}")

        # 7. Certificats SSL
        cert_specs = [
            ("partenaires.topnet.tn", "DigiCert Inc", Certificate.CertificateType.SINGLE, Certificate.Status.VALID, apps.get("Portail Partenaires & Revendeurs"), domains.get("partenaires.topnet.tn"), today + timedelta(days=180)),
            ("mail.topnet.tn", "DigiCert Global Root CA", Certificate.CertificateType.WILDCARD, Certificate.Status.EXPIRING, apps.get("Topnet Mail Pro (Zimbra)"), domains.get("mail.topnet.tn"), today + timedelta(days=14)),  # Alerte DSI !
            ("voip.topnet.tn", "Let's Encrypt Authority", Certificate.CertificateType.SINGLE, Certificate.Status.VALID, apps.get("Plateforme VoIP & Centre d'Appels"), domains.get("voip.topnet.tn"), today + timedelta(days=65)),
            ("sms-gw.topnet.tn", "Sectigo Limited", Certificate.CertificateType.SINGLE, Certificate.Status.VALID, apps.get("Passerelle SMS & OTP"), domains.get("sms-gw.topnet.tn"), today + timedelta(days=120)),
            ("soc.topnet.tn", "DigiCert Inc", Certificate.CertificateType.SINGLE, Certificate.Status.VALID, apps.get("Plateforme SOC & Détection d'Intrusions"), domains.get("soc.topnet.tn"), today + timedelta(days=240)),
        ]

        for cn, issuer, ctype, status, app, dom, exp in cert_specs:
            c, created = Certificate.objects.get_or_create(
                common_name=cn,
                defaults={
                    "issuer": issuer,
                    "certificate_type": ctype,
                    "status": status,
                    "application": app,
                    "domain": dom,
                    "issued_at": exp - timedelta(days=365),
                    "expires_at": exp,
                    "auto_renew": True,
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(f"  + Certificat SSL : {cn} (expire: {exp})")

        # 8. Contrats
        contract_specs = [
            (
                "CTR-2026-001",
                "Support & Maintenance Équipements Réseau Core Backbone",
                vendors.get("Cisco Systems"),
                apps.get("Supervision NMS & Cacti"),
                Contract.ContractType.SUPPORT,
                Contract.Status.ACTIVE,
                today - timedelta(days=90),
                today + timedelta(days=275),
                Decimal("95000.000"),
                achref_user,
            ),
            (
                "CTR-2026-002",
                "Licences Messagerie Zimbra Collaboration Pro (5 000 Boîtes)",
                vendors.get("Synacor (Zimbra)"),
                apps.get("Topnet Mail Pro (Zimbra)"),
                Contract.ContractType.LICENSE,
                Contract.Status.EXPIRING,
                today - timedelta(days=320),
                today + timedelta(days=22),  # Alerte DSI contrat < 30 jours !
                Decimal("48000.000"),
                ines_user,
            ),
            (
                "CTR-2026-003",
                "Garantie ProSupport Plus Serveurs Dell PowerEdge & Baies SAN",
                vendors.get("Dell Technologies"),
                apps.get("Plateforme VoIP & Centre d'Appels"),
                Contract.ContractType.MAINTENANCE,
                Contract.Status.ACTIVE,
                today - timedelta(days=60),
                today + timedelta(days=305),
                Decimal("62500.000"),
                system_user,
            ),
            (
                "CTR-2026-004",
                "Abonnement Sécurité UTM FortiGuard & Support Firewalls FortiGate",
                vendors.get("Fortinet"),
                apps.get("Plateforme SOC & Détection d'Intrusions"),
                Contract.ContractType.LICENSE,
                Contract.Status.ACTIVE,
                today - timedelta(days=120),
                today + timedelta(days=245),
                Decimal("38500.000"),
                admin_user,
            ),
        ]

        for ref, title, v, app, ctype, status, sdate, edate, cost, mgr in contract_specs:
            if v:
                c, created = Contract.objects.get_or_create(
                    reference=ref,
                    defaults={
                        "title": title,
                        "vendor": v,
                        "application": app,
                        "contract_type": ctype,
                        "status": status,
                        "start_date": sdate,
                        "end_date": edate,
                        "annual_cost": cost,
                        "currency": "TND",
                        "owner": mgr,
                        "auto_renew": False,
                        "is_active": True,
                    },
                )
                if created:
                    self.stdout.write(f"  + Contrat : {ref} - {title} ({cost} TND)")

        # 9. Incidents
        incident_specs = [
            (
                "Coupure temporaire du faisceau SIP Trunk vers opérateur externe",
                "Interruption de l'acheminement des appels sortants du centre de contact pendant 38 minutes.",
                Incident.Impact.CRITICAL,
                Incident.Status.RESOLVED,
                now - timedelta(days=4, hours=3),
                apps.get("Plateforme VoIP & Centre d'Appels"),
                system_user,
                "Micro-coupure fibre optique sur la boucle d'interconnexion métropolitaine.",
                "Basculement automatique de l'ensemble des routes SIP sur le trunk secondaire de secours.",
            ),
            (
                "Ralentissement d'accès au Webmail Zimbra lors du pic matinal",
                "Latence élevée (12 à 15 secondes) à l'ouverture de session pour plus de 800 collaborateurs.",
                Incident.Impact.MAJOR,
                Incident.Status.IN_PROGRESS,
                now - timedelta(hours=5),
                apps.get("Topnet Mail Pro (Zimbra)"),
                ines_user,
                "Saturation du pool de connexions LDAP et threads IMAP sous forte charge d'authentification.",
                "En cours d'optimisation : augmentation du cache memcached et redémarrage du service mailbox.",
            ),
            (
                "Échec d'envoi batch SMS de relance des factures impayées",
                "Blocage de la file d'attente d'envoi après 12 000 SMS distribués sur les 40 000 prévus.",
                Incident.Impact.MINOR,
                Incident.Status.CLOSED,
                now - timedelta(days=9),
                apps.get("Passerelle SMS & OTP"),
                achref_user,
                "Dépassement du débit maximal (TPS) autorisé par la passerelle de terminaison SMS.",
                "Throttling mis en place à 50 SMS/seconde avec temporisation dans RabbitMQ. File vidée avec succès.",
            ),
        ]

        for title, desc, imp, status, occ_at, app, rep_by, cause, sol in incident_specs:
            if app:
                inc, created = Incident.objects.get_or_create(
                    title=title,
                    application=app,
                    defaults={
                        "description": desc,
                        "impact": imp,
                        "status": status,
                        "occurred_at": occ_at,
                        "reported_by": rep_by,
                        "root_cause": cause,
                        "solution": sol,
                    },
                )
                if created:
                    self.stdout.write(f"  + Incident : [{imp}] {title}")

        # 10. Dépendances
        billing_app = apps.get("Billing")
        crm_app = apps.get("CRM Commercial")
        selfcare_app = apps.get("Selfcare Abonnés")
        b2b_app = apps.get("Portail Partenaires & Revendeurs")
        voip_app = apps.get("Plateforme VoIP & Centre d'Appels")
        sms_app = apps.get("Passerelle SMS & OTP")
        mail_app = apps.get("Topnet Mail Pro (Zimbra)")

        dep_specs = [
            (b2b_app, billing_app, Dependency.DependencyType.API, "Interrogation en temps réel des soldes et facturation des revendeurs"),
            (b2b_app, crm_app, Dependency.DependencyType.API, "Création automatique des fiches clients B2B et synchronisation des contrats"),
            (sms_app, selfcare_app, Dependency.DependencyType.API, "Vérification OTP lors des connexions à l'espace abonné"),
            (voip_app, crm_app, Dependency.DependencyType.API, "Remontée automatique de fiche client Topnet lors d'un appel entrant au support"),
            (mail_app, None, Dependency.DependencyType.AUTH, "Authentification LDAP / Active Directory pour les boîtes mails"),
        ]

        for source, target, dtype, desc in dep_specs:
            if source:
                defaults = {
                    "dependency_type": dtype,
                    "description": desc,
                    "is_active": True,
                }
                if target:
                    defaults["target_application"] = target
                    dep, created = Dependency.objects.get_or_create(
                        source_application=source,
                        target_application=target,
                        defaults=defaults,
                    )
                    target_name = target.name
                else:
                    defaults["target_external"] = "Active Directory LDAP"
                    dep, created = Dependency.objects.get_or_create(
                        source_application=source,
                        target_external="Active Directory LDAP",
                        defaults=defaults,
                    )
                    target_name = "Active Directory LDAP"

                if created:
                    self.stdout.write(f"  + Dépendance : {source.name} -> {target_name}")

        # 11. Documents & Tags
        tag_archi, _ = Tag.objects.get_or_create(name="Architecture")
        tag_sec, _ = Tag.objects.get_or_create(name="Sécurité")
        tag_pra, _ = Tag.objects.get_or_create(name="PCA / PRA")

        doc_specs = [
            (
                "Dossier d'Architecture Technique (DAT) — Plateforme VoIP Topnet",
                Document.Category.ARCHITECTURE,
                "Architecture VoIP haute disponibilité avec basculement SIP Trunk multi-sites.",
                apps.get("Plateforme VoIP & Centre d'Appels"),
                achref_user,
                [tag_archi],
            ),
            (
                "Plan de Continuité d'Activité (PCA) — Messagerie Zimbra Pro",
                Document.Category.PROCEDURE,
                "Procédure de basculement de secours et restauration des boîtes mails critiques.",
                apps.get("Topnet Mail Pro (Zimbra)"),
                ines_user,
                [tag_pra, tag_sec],
            ),
            (
                "Guide d'Intégration API — Passerelle SMS & OTP",
                Document.Category.OPS_MANUAL,
                "Documentation Swagger et spécifications techniques pour les développeurs internes.",
                apps.get("Passerelle SMS & OTP"),
                system_user,
                [tag_archi],
            ),
        ]

        for title, cat, desc, app, author, tags in doc_specs:
            if app:
                doc, created = Document.objects.get_or_create(
                    title=title,
                    application=app,
                    defaults={
                        "category": cat,
                        "description": desc,
                        "uploaded_by": author,
                        "file_type": "PDF",
                    },
                )
                if created:
                    for tag in tags:
                        doc.tags.add(tag)
                    self.stdout.write(f"  + Document : {title}")

        # 12. Notifications DSI
        notif_specs = [
            (
                achref_user,
                "Alerte Certificat SSL : mail.topnet.tn",
                "Le certificat SSL *.topnet.tn pour Zimbra expire dans moins de 15 jours. Merci de planifier le renouvellement.",
                Notification.NotificationType.EXPIRY,
                "/certificates/",
            ),
            (
                ines_user,
                "Échéance Contrat Imminente : Zimbra Collaboration Pro",
                "Le contrat CTR-2026-002 avec Synacor arrive à échéance dans 22 jours. Procéder à la validation du bon de commande.",
                Notification.NotificationType.EXPIRY,
                "/contracts/",
            ),
            (
                admin_user,
                "Incident Majeur DSI : Ralentissement Webmail",
                "Une cellule de support est active sur l'incident d'accès Webmail. MTTR estimé : 45 minutes.",
                Notification.NotificationType.INCIDENT,
                "/incidents/",
            ),
        ]

        for u, title, msg, ntype, link in notif_specs:
            if u:
                Notification.objects.create(
                    user=u,
                    title=title,
                    message=msg,
                    notification_type=ntype,
                    link=link,
                    status=Notification.Status.UNREAD,
                )

        self.stdout.write(self.style.SUCCESS("==> Nouvelles données DSI Topnet insérées avec succès !"))
