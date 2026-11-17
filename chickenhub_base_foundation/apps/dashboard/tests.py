from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class DashboardAccessTests(TestCase):
    """Tests for dashboard protection and public views."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner_user',
            password='Password123!',
            role=User.Role.OWNER,
            is_staff=True,
        )
        self.employee = User.objects.create_user(
            username='employee_user',
            password='Password123!',
            role=User.Role.EMPLOYEE,
            is_staff=True,
        )
        self.dashboard_url = reverse('dashboard:index')
        self.public_home_url = reverse('public:home')

    def test_public_home_accessible_without_login(self):
        response = self.client.get(self.public_home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'public/home.html')
        self.assertContains(response, 'ChickenHub')
        self.assertContains(response, 'Braaied Chicken Dust')

    def test_unauthenticated_user_redirected_from_dashboard(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_authenticated_staff_can_access_dashboard(self):
        self.client.login(username='employee_user', password='Password123!')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/index.html')
        self.assertIn("Today's Sales", response.content.decode())
        self.assertContains(response, 'Pending Orders')
        self.assertContains(response, 'Stock Items')
        self.assertContains(response, 'Low-Stock Items')
