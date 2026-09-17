from django.contrib.auth.models import UserManager as DjangoUserManager


class UserManager(DjangoUserManager):
    """Optional override for future custom user model."""

    def create_staff_user(self, username, password, role, **extra):
        from users.models import UserProfile

        user = self.create_user(username=username, password=password, **extra)
        UserProfile.objects.create(user=user, role=role)
        return user
