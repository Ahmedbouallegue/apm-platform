from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.dashboard.selectors.dashboard import dashboard_stats

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
