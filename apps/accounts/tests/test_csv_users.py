from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.services.csv_users import users_from_csv, users_to_csv

User = get_user_model()


class CsvUsersUnitTests(TestCase):
    def setUp(self):
        self.actor = User.objects.create_user(
            username="csvactor",
            password="Secret123!",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.existing = User.objects.create_user(
            username="exist",
            email="exist@topnet.tn",
            password="Secret123!",
            role=User.Role.VIEWER,
            department="Ops",
        )

    def test_users_to_csv_headers_and_row(self):
        content = users_to_csv([self.existing])
        lines = content.strip().split("\n")
        self.assertTrue(lines[0].startswith("username,email,first_name"))
        self.assertIn("exist,exist@topnet.tn", content)
        self.assertIn(",viewer,", content)

    def test_users_from_csv_creates_with_role_alias(self):
        csv_data = (
            "username,email,first_name,last_name,role,phone,department,is_active,password\n"
            "tech1,tech1@topnet.tn,Tech,One,technicien,,DSI,1,Secret123!\n"
        )
        result = users_from_csv(content=csv_data, actor=self.actor)
        self.assertEqual(result.created, 1)
        self.assertEqual(result.errors, [])
        user = User.objects.get(username="tech1")
        self.assertEqual(user.role, User.Role.MANAGER)

    def test_users_from_csv_updates_existing(self):
        csv_data = (
            "username,email,first_name,last_name,role,phone,department,is_active,password\n"
            "exist,new@topnet.tn,New,Name,lecteur,,Finance,1,\n"
        )
        result = users_from_csv(content=csv_data, actor=self.actor)
        self.assertEqual(result.updated, 1)
        self.existing.refresh_from_db()
        self.assertEqual(self.existing.email, "new@topnet.tn")
        self.assertEqual(self.existing.role, User.Role.VIEWER)
        self.assertEqual(self.existing.department, "Finance")

    def test_users_from_csv_invalid_role(self):
        csv_data = (
            "username,email,first_name,last_name,role,phone,department,is_active,password\n"
            "bad,bad@topnet.tn,,,pirate,,DSI,1,Secret123!\n"
        )
        result = users_from_csv(content=csv_data, actor=self.actor)
        self.assertEqual(result.created, 0)
        self.assertTrue(any("Rôle invalide" in err for err in result.errors))

    def test_users_from_csv_missing_username_header(self):
        result = users_from_csv(content="email,role\nx@y.z,viewer\n")
        self.assertTrue(any("username" in err for err in result.errors))
