from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserModelTests(TestCase):
    """Unit tests for the custom User model and role-based helper properties."""

    def test_create_employee_user(self):
        user = User.objects.create_user(
            username='chef_sipho',
            password='TestPassword123!',
            first_name='Sipho',
            last_name='Dlamini',
            role=User.Role.EMPLOYEE,
        )
        self.assertEqual(user.username, 'chef_sipho')
        self.assertEqual(user.role, User.Role.EMPLOYEE)
        self.assertTrue(user.is_employee)
        self.assertFalse(user.is_manager)
        self.assertFalse(user.is_owner)
        self.assertEqual(str(user), 'Sipho Dlamini (Employee)')

    def test_create_manager_user(self):
        user = User.objects.create_user(
            username='manager_lerato',
            password='TestPassword123!',
            first_name='Lerato',
            last_name='Khumalo',
            role=User.Role.MANAGER,
        )
        self.assertEqual(user.role, User.Role.MANAGER)
        self.assertTrue(user.is_employee)
        self.assertTrue(user.is_manager)
        self.assertFalse(user.is_owner)

    def test_create_owner_user(self):
        user = User.objects.create_user(
            username='owner_melusi',
            password='TestPassword123!',
            first_name='Melusi',
            last_name='Nkosi',
            role=User.Role.OWNER,
        )
        self.assertEqual(user.role, User.Role.OWNER)
        self.assertTrue(user.is_employee)
        self.assertTrue(user.is_manager)
        self.assertTrue(user.is_owner)

    def test_create_superuser_assigns_owner_role(self):
        admin = User.objects.create_superuser(
            username='superadmin',
            email='admin@chickenhub.co.za',
            password='AdminPassword123!',
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.role, User.Role.OWNER)
        self.assertTrue(admin.is_owner)
        self.assertTrue(admin.is_manager)
        self.assertTrue(admin.is_employee)


class AuthenticationViewTests(TestCase):
    """Tests for staff login, logout, and access protection."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='StrongPassword123!',
            role=User.Role.EMPLOYEE,
            is_staff=True,
        )
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.dashboard_url = reverse('dashboard:index')

    def test_login_page_renders_successfully(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        self.assertContains(response, 'Staff Management Portal')

    def test_successful_staff_login(self):
        response = self.client.post(
            self.login_url,
            {'username': 'staffuser', 'password': 'StrongPassword123!'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertTemplateUsed(response, 'dashboard/index.html')

    def test_invalid_login_credentials(self):
        response = self.client.post(
            self.login_url,
            {'username': 'staffuser', 'password': 'WrongPassword'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        self.assertFalse(response.context['user'].is_authenticated)

    def test_logout_redirects_to_home(self):
        self.client.login(username='staffuser', password='StrongPassword123!')
        response = self.client.post(self.logout_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertTemplateUsed(response, 'public/home.html')


class RoleBasedAccessDecoratorTests(TestCase):
    """Tests for role_required, owner_required, manager_required decorators."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner_user',
            password='Password123!',
            role=User.Role.OWNER,
        )
        self.manager = User.objects.create_user(
            username='manager_user',
            password='Password123!',
            role=User.Role.MANAGER,
        )
        self.employee = User.objects.create_user(
            username='employee_user',
            password='Password123!',
            role=User.Role.EMPLOYEE,
        )

    def test_decorator_enforcement(self):
        from django.http import HttpResponse
        from apps.accounts.decorators import owner_required, manager_required, staff_required
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage

        factory = RequestFactory()

        @owner_required
        def dummy_owner_view(request):
            return HttpResponse("Owner Only Content")

        @manager_required
        def dummy_manager_view(request):
            return HttpResponse("Manager Content")

        # 1. Unauthenticated request -> redirects to login
        request = factory.get('/dummy/')
        request.user = self.employee
        # Attach message framework
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # Employee accessing owner view -> redirects to dashboard
        response = dummy_owner_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:index'))

        # Owner accessing owner view -> succeeds (200)
        request.user = self.owner
        response = dummy_owner_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Owner Only Content")

        # Manager accessing manager view -> succeeds (200)
        request.user = self.manager
        response = dummy_manager_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Manager Content")
