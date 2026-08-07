from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()

class ProfileWebTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="meuser",
            password="Secret123!",
            role=User.Role.MANAGER,
            first_name="Achref",
            last_name="Benali",
        )

    def test_profile_button_on_home(self):
        self.client.login(username="meuser", password="Secret123!")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/profile/")
        self.assertContains(response, "Mon profil")
        self.assertContains(response, "Achref")
        self.assertContains(response, "Benali")
        self.assertContains(response, "Déconnexion")
        self.assertContains(response, "user-menu-dropdown")

    def test_profile_page(self):
        self.client.login(username='meuser', password='Secret123!')
        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mon profil')
        self.assertContains(response, 'Achref')
