from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from .forms import StaffLoginForm


class StaffLoginView(View):
    """
    Staff login view providing authentication for Owner, Manager and Employee accounts.
    """
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            messages.info(
                request,
                f"You are already logged in as {request.user.get_full_name() or request.user.username}."
            )
            return redirect('dashboard:index')

        form = StaffLoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')

        form = StaffLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(
                request,
                f"Welcome back, {user.get_full_name() or user.username}! Logged in as {user.get_role_display()}."
            )
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard:index')

        messages.error(
            request,
            "Invalid username or password. Please check your credentials and try again."
        )
        return render(request, self.template_name, {'form': form})


class StaffLogoutView(View):
    """
    Staff logout view. Safely ends session and redirects to public home page.
    Supports both POST (recommended) and GET for convenience.
    """
    def post(self, request):
        if request.user.is_authenticated:
            user_name = request.user.get_full_name() or request.user.username
            auth_logout(request)
            messages.success(request, f"Goodbye, {user_name}. You have been logged out.")
        return redirect('public:home')

    def get(self, request):
        # Support graceful GET fallback with confirmation redirect
        return self.post(request)
