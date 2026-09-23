import factory

from accounting.models import Account


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Account

    account_code = factory.Sequence(lambda n: f"{9000 + n}")
    account_name = factory.Sequence(lambda n: f"Test Account {n}")
    account_type = "ASSET"
    status = "ACTIVE"
