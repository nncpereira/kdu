import factory

from governance.models import GlobalConfig


class GlobalConfigFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GlobalConfig

    parameter_key = factory.Sequence(lambda n: f"param_{n}")
    parameter_value = {"value": 1}
    effective_from = "2025-01-01"
    status = "ACTIVE"
    created_by = factory.SubFactory("tests.factories.SuperadminProfileFactory")
