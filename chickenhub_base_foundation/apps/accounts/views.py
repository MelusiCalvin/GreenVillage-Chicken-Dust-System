from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout, get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views import View
from .forms import StaffLoginForm, StaffUserCreationForm, StaffUserUpdateForm, StaffPasswordResetForm
from .decorators import OwnerRequiredMixin

User = get_user_model()


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


# ---------------------------------------------------------------------------
# Staff Account Management Views (Owner only)
# ---------------------------------------------------------------------------

class StaffListView(OwnerRequiredMixin, View):
    """
    Lists all staff accounts. Accessible by Owners only.
    """
    template_name = 'accounts/staff_list.html'

    def get(self, request):
        staff_users = User.objects.all().order_by('role', 'last_name', 'first_name')
        return render(request, self.template_name, {'staff_users': staff_users})


class StaffCreateView(OwnerRequiredMixin, View):
    """
    Allows the Owner to create a new staff account.
    """
    template_name = 'accounts/staff_form.html'

    def get(self, request):
        form = StaffUserCreationForm()
        return render(request, self.template_name, {
            'form': form,
            'form_title': 'Add New Staff Member',
            'submit_label': 'Create Account',
        })

    def post(self, request):
        form = StaffUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Staff account for {user.get_full_name() or user.username} "
                f"({user.get_role_display()}) created successfully."
            )
            return redirect('accounts:staff_list')

        messages.error(request, "Please correct the errors below and try again.")
        return render(request, self.template_name, {
            'form': form,
            'form_title': 'Add New Staff Member',
            'submit_label': 'Create Account',
        })


class StaffDetailView(OwnerRequiredMixin, View):
    """
    Displays the profile details of a single staff member.
    """
    template_name = 'accounts/staff_detail.html'

    def get(self, request, pk):
        staff_member = get_object_or_404(User, pk=pk)
        return render(request, self.template_name, {'staff_member': staff_member})


class StaffUpdateView(OwnerRequiredMixin, View):
    """
    Allows the Owner to update a staff member's profile, role and active status.
    """
    template_name = 'accounts/staff_form.html'

    def get(self, request, pk):
        staff_member = get_object_or_404(User, pk=pk)
        form = StaffUserUpdateForm(instance=staff_member)
        return render(request, self.template_name, {
            'form': form,
            'form_title': f'Edit Staff — {staff_member.get_full_name() or staff_member.username}',
            'submit_label': 'Save Changes',
            'staff_member': staff_member,
        })

    def post(self, request, pk):
        staff_member = get_object_or_404(User, pk=pk)
        form = StaffUserUpdateForm(request.POST, instance=staff_member)
        if form.is_valid():
            updated = form.save()
            messages.success(
                request,
                f"Staff account for {updated.get_full_name() or updated.username} updated successfully."
            )
            return redirect('accounts:staff_detail', pk=pk)

        messages.error(request, "Please correct the errors below and try again.")
        return render(request, self.template_name, {
            'form': form,
            'form_title': f'Edit Staff — {staff_member.get_full_name() or staff_member.username}',
            'submit_label': 'Save Changes',
            'staff_member': staff_member,
        })


class StaffDeactivateView(OwnerRequiredMixin, View):
    """
    Toggles the active/inactive status of a staff account (POST only).
    Prevents the owner from deactivating their own account.
    """
    def post(self, request, pk):
        staff_member = get_object_or_404(User, pk=pk)

        # Prevent owner from locking themselves out
        if staff_member == request.user:
            messages.error(request, "You cannot deactivate your own account.")
            return redirect('accounts:staff_detail', pk=pk)

        staff_member.is_active = not staff_member.is_active
        staff_member.save(update_fields=['is_active'])

        action = "activated" if staff_member.is_active else "deactivated"
        messages.success(
            request,
            f"Account for {staff_member.get_full_name() or staff_member.username} has been {action}."
        )
        return redirect('accounts:staff_detail', pk=pk)


class StaffPasswordResetView(OwnerRequiredMixin, View):
    """
    Allows the Owner to set a new password for any staff member.
    """
    template_name = 'accounts/staff_password_reset.html'

    def get(self, request, pk):
        staff_member = get_object_or_404(User, pk=pk)
        form = StaffPasswordResetForm(user=staff_member)
        return render(request, self.template_name, {
            'form': form,
            'staff_member': staff_member,
        })

    def post(self, request, pk):
        staff_member = get_object_or_404(User, pk=pk)
        form = StaffPasswordResetForm(user=staff_member, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Password for {staff_member.get_full_name() or staff_member.username} "
                f"has been reset successfully."
            )
            return redirect('accounts:staff_detail', pk=pk)

        messages.error(request, "Please correct the errors below and try again.")
        return render(request, self.template_name, {
            'form': form,
            'staff_member': staff_member,
        })
