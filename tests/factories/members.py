from decimal import Decimal

import factory

from members.models import Member


class MemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Member

    salutation = "Mr"
    first_name = factory.Sequence(lambda n: f"First{n}")
    middle_name = ""
    last_name = "Doe"
    national_id = factory.Sequence(lambda n: f"N{n:06d}")
    phone_number = factory.Sequence(lambda n: f"77000{n:03d}")
    email = None
    date_of_birth = "1990-01-01"
    aldeia = "A"
    suco = "S"
    posto = "P"
    municipio = "Dili"
    profession = "Vendor"
    status = Member.Status.ACTIVE
    kapital_sosial_balance = Decimal("50.00")
    date_joined = "2025-01-01"
