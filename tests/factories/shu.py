from decimal import Decimal

import factory

from shu.models import ShuFiscalYear, ShuWeightingBase


class ShuFiscalYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShuFiscalYear

    year_start = "2025-07-01"
    year_end = "2026-06-30"
    status = ShuFiscalYear.Status.OPEN
    net_surplus = Decimal("130461.20")
    kapital_sosial = Decimal("1259361.74")
    accumulated_reserva_legal = Decimal("1300000.00")


class ShuWeightingBaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShuWeightingBase

    fy = factory.SubFactory(ShuFiscalYearFactory)
    member = factory.SubFactory("tests.factories.MemberFactory")
    sum_weighted_balance = Decimal("780000.00")
    months_active = 12
    weighted_savings_units = Decimal("65000.00")
    loan_interest_paid = Decimal("600.00")
