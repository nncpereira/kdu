from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from users.models import UserProfile


@require_http_methods(["GET", "POST"])
def staff_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if (
            user
            and hasattr(user, "profile")
            and user.profile.role != UserProfile.Role.MEMBER
        ):
            login(request, user)
            if user.profile.must_change_password:
                return redirect("staff-change-password")
            return redirect("admin:index")
        return render(request, "users/login.html", {"error": "Invalid credentials."})
    return render(request, "users/login.html")


@require_http_methods(["GET", "POST"])
def member_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if (
            user
            and hasattr(user, "profile")
            and user.profile.role == UserProfile.Role.MEMBER
        ):
            login(request, user)
            if user.profile.must_change_password:
                return redirect("member-change-password")
            return redirect("member-dashboard")
        return render(request, "users/login.html", {"error": "Invalid credentials."})
    return render(request, "users/login.html")


@login_required
def logout_session(request):
    logout(request)
    return redirect("staff-login")


@login_required
@require_http_methods(["GET", "POST"])
def change_password(request):
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        if not new_password or len(new_password) < 8:
            return render(
                request,
                "users/change_password.html",
                {"error": "Password must be at least 8 characters."},
            )
        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])

        profile = request.user.profile
        profile.must_change_password = False
        profile.save(update_fields=["must_change_password"])

        return redirect(
            "admin:index"
            if profile.role != UserProfile.Role.MEMBER
            else "member-dashboard"
        )
    return render(request, "users/change_password.html")
