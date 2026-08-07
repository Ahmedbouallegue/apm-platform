from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.audit.models import AuditLog
from apps.contracts.models import Contract
from apps.contracts.services.contracts import (
    contract_create,
    contract_soft_delete,
    contract_update,
)
from apps.vendors.models import Vendor

User = get_user_model()


class ContractServiceUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ctrsvc", password="Secret123!", role=User.Role.MANAGER
        )
        self.vendor = Vendor.objects.create(
            name="Oracle",
            vendor_type=Vendor.VendorType.SOFTWARE,
        )

    def test_create_update_soft_delete(self):
        start = date.today()
        end = start + timedelta(days=365)
        contract = contract_create(
            data={
                "reference": "CTR-UNIT-01",
                "title": "Support Oracle",
                "vendor": self.vendor,
                "contract_type": Contract.ContractType.MAINTENANCE,
                "status": Contract.Status.ACTIVE,
                "start_date": start,
                "end_date": end,
                "annual_cost": Decimal("5000.000"),
                "currency": "TND",
                "auto_renew": True,
            },
            user=self.user,
        )
        self.assertTrue(contract.auto_renew)
        self.assertTrue(
            AuditLog.objects.filter(
                action="create", entity="Contract", entity_id=str(contract.pk)
            ).exists()
        )

        contract_update(
            contract=contract,
            data={"title": "Support Oracle DB"},
            user=self.user,
        )
        contract.refresh_from_db()
        self.assertEqual(contract.title, "Support Oracle DB")

        contract_soft_delete(contract=contract, user=self.user)
        contract.refresh_from_db()
        self.assertTrue(contract.is_deleted)
