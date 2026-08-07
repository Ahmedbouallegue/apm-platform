from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.contracts.models import Contract
from apps.vendors.models import Vendor

User = get_user_model()


class ContractAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username="ctrmgr",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        self.vendor = Vendor.objects.create(
            name="IBM Support",
            vendor_type=Vendor.VendorType.MAINTENANCE,
        )

    def test_create_contract(self):
        self.client.force_authenticate(self.manager)
        start = date.today()
        end = start + timedelta(days=365)
        response = self.client.post(
            "/api/contracts/",
            {
                "reference": "CTR-2026-001",
                "title": "Maintenance CRM",
                "vendor": self.vendor.pk,
                "contract_type": "maintenance",
                "status": "active",
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "annual_cost": "12000.000",
                "currency": "TND",
                "sla_level": "24/7",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        contract = Contract.objects.get(reference="CTR-2026-001")
        self.assertEqual(contract.vendor_id, self.vendor.pk)
        self.assertEqual(contract.annual_cost, Decimal("12000.000"))


class ContractWebTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="webctr",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        vendor = Vendor.objects.create(name="Microsoft", vendor_type=Vendor.VendorType.SOFTWARE)
        Contract.objects.create(
            reference="CTR-WEB-01",
            title="Licences M365",
            vendor=vendor,
            contract_type=Contract.ContractType.LICENSE,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
        )

    def test_list_page(self):
        self.client.login(username="webctr", password="Secret123!")
        response = self.client.get("/contracts/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contrats")
        self.assertContains(response, "CTR-WEB-01")
