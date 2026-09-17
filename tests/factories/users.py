import factory
from django.contrib.auth import get_user_model

from users.models import UserProfile

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    is_active = True


class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    role = UserProfile.Role.MAKER
    must_change_password = False


class MakerProfileFactory(UserProfileFactory):
    role = UserProfile.Role.MAKER


class CheckerProfileFactory(UserProfileFactory):
    role = UserProfile.Role.CHECKER


class CertifierProfileFactory(UserProfileFactory):
    role = UserProfile.Role.CERTIFIER


class SuperadminProfileFactory(UserProfileFactory):
    role = UserProfile.Role.SUPERADMIN
