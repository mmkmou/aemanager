# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from contact.models import Address
from django.db.models.signals import post_save
import datetime

AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC = 1
AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC = 2
AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC = 3
AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC = 4
AUTOENTREPRENEUR_ACTIVITY = ((AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC, _('Product sale (BIC)')),
                             (AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC, _('Provision of a service (BIC)')),
                             (AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC, _('Provision of a service (BNC)')),
                             (AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC, _('Liberal profession (BNC)')))

class SalesLimit(models.Model):
    year = models.IntegerField(verbose_name=_('Year'))
    activity = models.IntegerField(choices=AUTOENTREPRENEUR_ACTIVITY,
                                   verbose_name=_('Activity'))
    limit = models.IntegerField(verbose_name=_('Limit'))
    limit2 = models.IntegerField(verbose_name=_('Limit 2'))

AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY = 1
AUTOENTREPRENEUR_PAYMENT_OPTION_MONTHLY = 2
AUTOENTREPRENEUR_PAYMENT_OPTION = ((AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY, _('Quaterly')),
                                   (AUTOENTREPRENEUR_PAYMENT_OPTION_MONTHLY, _('Monthly')))

TAX_RATE_WITH_FREEING = {AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC: [4, 7, 10, 13],
                         AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC: [7.1, 12.4, 17.7, 23],
                         AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC: [7.6, 12.9, 18.2, 23.5],
                         AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC: [7.5, 11.4, 16, 20.5]
                         }

TAX_RATE_WITHOUT_FREEING = {AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC: [3, 6, 9, 12],
                            AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC: [5.4, 10.7, 16, 21.3],
                            AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC: [5.4, 10.7, 16, 21.3],
                            AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC: [5.3, 9.2, 13.8, 18.3]
                            }

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    company_name = models.CharField(max_length=255, blank=True, default='', verbose_name=_('Company name'))
    company_id = models.CharField(max_length=50, blank=True, default='', verbose_name=_('Company id')) # SIRET for France
    bank_information = models.CharField(max_length=255, blank=True, default='', verbose_name=_('Bank information'))
    address = models.ForeignKey(Address, verbose_name=_('Address'))
    activity = models.IntegerField(choices=AUTOENTREPRENEUR_ACTIVITY, blank=True, null=True, verbose_name=_('Activity'))
    creation_date = models.DateField(blank=True, null=True, verbose_name=_('Creation date'))
    creation_help = models.BooleanField(verbose_name=_('Creation help')) # accre
    freeing_tax_payment = models.BooleanField(verbose_name=_('Freeing tax payment')) # versement liberatoire
    payment_option = models.IntegerField(choices=AUTOENTREPRENEUR_PAYMENT_OPTION, blank=True, null=True, verbose_name=_('Payment option'))

    def settings_defined(self):
        settings_defined = False
        if self.user.first_name \
            and self.user.last_name \
            and self.company_id \
            and self.address.street \
            and self.address.zipcode \
            and self.address.city \
            and self.activity \
            and self.creation_date \
            and self.payment_option:

            settings_defined = True

        return settings_defined

    def get_sales_limit(self, year=None):
        today = datetime.date.today()
        limit = 0
        if not year:
            year = today.year
        if self.activity:
            limit = SalesLimit.objects.get(year=year, activity=self.activity).limit
            if self.creation_date and self.creation_date.year == year:
                worked_days = datetime.date(year + 1, 1, 1) - self.creation_date
                days_in_year = datetime.date(year + 1, 1, 1) - datetime.date(year, 1, 1)
                limit = int(round(float(limit) * worked_days.days / days_in_year.days))
        return limit

    def get_service_sales_limit(self, year=None):
        today = datetime.date.today()
        service_limit = 0
        if not year:
            year = today.year
        if self.activity == AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC:
            service_limit = SalesLimit.objects.get(year=year, activity=AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC).limit
            if self.creation_date and self.creation_date.year == year:
                worked_days = datetime.date(year + 1, 1, 1) - self.creation_date
                days_in_year = datetime.date(year + 1, 1, 1) - datetime.date(year, 1, 1)
                service_limit = int(round(float(service_limit) * worked_days.days / days_in_year.days))
        return service_limit

    def get_quarter(self, date):
        return ((date.month + 2) // 3, date.year)

    def get_next_quarter(self, quarter, year):
        next_quarter = quarter % 4 + 1
        next_year = year
        if quarter == 4:
            next_year = next_year + 1
        return (next_quarter, next_year)

    def get_first_period_payment_date(self):
        if self.payment_option == AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY:
            first_quarter = self.get_quarter(self.creation_date)
            second_quarter = self.get_next_quarter(first_quarter[0], first_quarter[1])
            third_quarter = self.get_next_quarter(second_quarter[0], second_quarter[1])
            payment_date = datetime.date(third_quarter[1], third_quarter[0] * 3 - 1, 1) - datetime.timedelta(1)
        else:
            payment_date = datetime.date(self.creation_date.year + self.creation_date.month // 9,
                                         (self.creation_date.month + 3) % 12 + 1,
                                         1)
        return payment_date

    def get_period_for_tax(self, reference_date=None):
        begin_date = end_date = None
        current_date = reference_date or datetime.date.today()
        first_period = False
        first_payment_date = self.get_first_period_payment_date()
        if current_date <= first_payment_date:
            current_date = first_payment_date
            first_period = True

        if self.payment_option == AUTOENTREPRENEUR_PAYMENT_OPTION_MONTHLY:
            if current_date.month == 1:
                begin_date = datetime.date(current_date.year - 1, 12, 1)
                end_date = datetime.date(current_date.year - 1, 12, 31)
            else:
                begin_date = datetime.date(current_date.year, current_date.month - 1, 1)
                end_date = datetime.date(current_date.year, current_date.month, 1) - datetime.timedelta(1)

        elif self.payment_option == AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY:
            if current_date.month == 1:
                begin_date = datetime.date(current_date.year - 1, 10, 1)
                end_date = datetime.date(current_date.year - 1, 12, 31)
            elif current_date.month <= 4:
                begin_date = datetime.date(current_date.year, 1, 1)
                end_date = datetime.date(current_date.year, 3, 31)
            elif current_date.month <= 7:
                begin_date = datetime.date(current_date.year, 4, 1)
                end_date = datetime.date(current_date.year, 6, 30)
            elif current_date.month <= 10:
                begin_date = datetime.date(current_date.year, 7, 1)
                end_date = datetime.date(current_date.year, 9, 30)
            else:
                begin_date = datetime.date(current_date.year, 10, 1)
                end_date = datetime.date(current_date.year, 12, 31)
        if first_period:
            begin_date = self.creation_date

        return begin_date, end_date

    def get_tax_rate(self, reference_date=None):
        tax_rate = 0
        if not self.activity:
            return tax_rate
        today = reference_date or datetime.date.today()

        if self.creation_help:
            year = self.creation_date.year + 1
            month = self.get_quarter(self.creation_date)[0] * 3 - 1
            first_period_end_date = datetime.date(year, month, 1) - datetime.timedelta(1)
            second_period_end_date = datetime.date(first_period_end_date.year + 1,
                                                   first_period_end_date.month,
                                                   first_period_end_date.day)
            third_period_end_date = datetime.date(first_period_end_date.year + 2,
                                                   first_period_end_date.month,
                                                   first_period_end_date.day)
            if today <= first_period_end_date:
                if self.freeing_tax_payment:
                    tax_rate = TAX_RATE_WITH_FREEING[self.activity][0]
                else:
                    tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][0]
            elif today <= second_period_end_date:
                if self.freeing_tax_payment:
                    tax_rate = TAX_RATE_WITH_FREEING[self.activity][1]
                else:
                    tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][1]
            elif today <= third_period_end_date:
                if self.freeing_tax_payment:
                    tax_rate = TAX_RATE_WITH_FREEING[self.activity][2]
                else:
                    tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][2]

            else:
                if self.freeing_tax_payment:
                    tax_rate = TAX_RATE_WITH_FREEING[self.activity][3]
                else:
                    tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][3]
        else:
            if self.freeing_tax_payment:
                tax_rate = TAX_RATE_WITH_FREEING[self.activity][3]
            else:
                tax_rate = TAX_RATE_WITHOUT_FREEING[self.activity][3]

        return tax_rate

    def get_pay_date(self, end_date=None):
        pay_date = None
        if end_date:
            year = end_date.year
            if end_date.month == 12:
                year = year + 1
            pay_date = datetime.date(year,
                                     (end_date.month + 2) % 12 or 12,
                                     1) - datetime.timedelta(1)
        return pay_date

def user_post_save(sender, instance, created, **kwargs):
    if created:
        try:
            profile = UserProfile.objects.get(user=instance)
        except:
            address = Address()
            address.save(user=instance)
            profile = UserProfile()
            profile.user = instance
            profile.address = address
            profile.save()

post_save.connect(user_post_save, sender=User)
