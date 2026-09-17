from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
# from .models import UserProfile
from users.models import UserProfile


User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0
    fields = ("role", "must_change_password")
    readonly_fields = ("created_at", "updated_at")


# Replace Django's default User admin with the profile-aware admin.
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = [UserProfileInline]
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "get_role",
        "is_active",
        "is_staff",
    )
    list_filter = ("is_active", "is_staff", "profile__role")

    def get_role(self, obj):
        return getattr(obj.profile, "role", "—")

    get_role.short_description = "Role"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "must_change_password", "created_at")
    list_filter = ("role", "must_change_password")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")
