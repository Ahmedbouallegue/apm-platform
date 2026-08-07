from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.applications.models import Application
from apps.certificates.models import Certificate
from apps.dashboard.selectors.dashboard import _health_score, dashboard_stats
from apps.incidents.models import Incident

User = get_user_model()

CHART_KEYS = [
    "apps_by_status",
    "apps_by_criticality",
    "incidents_by_status",
    "incidents_by_impact",
    "documents_by_category",
    "certs_expiry_buckets",
    "contracts_by_status",
    "portfolio_overview",
    "incidents_trend_6m",
    "apps_trend_6m",
]


class DashboardAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="dashmgr", password="Secret123!", role=User.Role.MANAGER
        )

    def test_stats_endpoint(self):
        self.client.force_authenticate(self.manager)
        response = self.client.get("/api/dashboard/stats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("apps_total", response.data)
        self.assertIn("incidents_open", response.data)
        self.assertIn("documents_total", response.data)
        self.assertIn("charts", response.data)
        for key in CHART_KEYS:
            self.assertIn(key, response.data["charts"])
            series = response.data["charts"][key]
            self.assertIn("labels", series)
            self.assertIn("values", series)
            self.assertEqual(len(series["labels"]), len(series["values"]))


class DashboardSelectorTests(TestCase):
    def test_charts_structure(self):
        stats = dashboard_stats()
        self.assertIn("charts", stats)
        apps_status = stats["charts"]["apps_by_status"]
        self.assertEqual(len(apps_status["labels"]), len(apps_status["values"]))
        self.assertEqual(len(stats["charts"]["apps_trend_6m"]["labels"]), 6)
        self.assertEqual(len(stats["charts"]["certs_expiry_buckets"]["labels"]), 4)

    def test_health_score_healthy_by_default(self):
        health = _health_score(
            incidents_open=0,
            incidents_critical=0,
            certs_expiring=0,
            certs_expired=0,
            domains_expiring=0,
            contracts_expiring=0,
        )
        self.assertEqual(health["score"], 100)
        self.assertEqual(health["level"], "ok")
        self.assertEqual(health["label"], "Sain")

    def test_health_score_drops_with_critical_incidents(self):
        health = _health_score(
            incidents_open=2,
            incidents_critical=2,
            certs_expiring=0,
            certs_expired=0,
            domains_expiring=0,
            contracts_expiring=0,
        )
        self.assertEqual(health["score"], 70)
        self.assertEqual(health["level"], "warn")

    def test_stats_include_health_and_upcoming(self):
        today = timezone.localdate()
        Certificate.objects.create(
            common_name="soon.topnet.tn",
            expires_at=today + timedelta(days=15),
            status=Certificate.Status.VALID,
        )
        app = Application.objects.create(
            name="Prod App",
            status=Application.Status.PRODUCTION,
            criticality=Application.Criticality.HIGH,
        )
        Incident.objects.create(
            title="Outage",
            description="Panne critique",
            occurred_at=timezone.now(),
            status=Incident.Status.OPEN,
            impact=Incident.Impact.CRITICAL,
            application=app,
        )
        stats = dashboard_stats()
        self.assertIn("health", stats)
        self.assertIn("score", stats["health"])
        self.assertIn("upcoming_expiries", stats)
        self.assertGreaterEqual(len(stats["upcoming_expiries"]), 1)
        self.assertEqual(stats["upcoming_expiries"][0]["kind_key"], "cert")
        self.assertGreaterEqual(stats["incidents_critical"], 1)


class DashboardWebTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="webdash", password="Secret123!", role=User.Role.MANAGER
        )

    def test_dashboard_page(self):
        self.client.login(username="webdash", password="Secret123!")
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "dashboard-charts.js")
        self.assertContains(response, "chart.js")
        self.assertContains(response, 'id="chart-portfolio"')
        self.assertContains(response, "dashboard-charts-data")
        self.assertContains(response, "Analyses graphiques")

    def test_home_page_shows_health_score(self):
        self.client.login(username="webdash", password="Secret123!")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "health-meter")
        self.assertContains(response, "home-charts.js")
        self.assertContains(response, "home-charts-data")
        self.assertContains(response, "Sain")
