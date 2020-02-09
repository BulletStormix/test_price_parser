from django.utils import timezone
import pytz

from django.contrib.auth.models import User
from django.db import models, transaction

# from parsing.constants import Identifier
# from parsing.constants import PageParser


class Site(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sites')
    url = models.URLField()
    photo_path = models.CharField(max_length=200, null=True, blank=True)
    is_running = models.BooleanField(default=False)

    def get_prices(self):
        return Price.objects.filter(site=self).order_by('-date')

    @property
    def last_price(self):
        prices = self.get_prices()
        return prices.first() if prices.exists() else None

    @transaction.atomic
    def add_price_and_photo(self, price, photoname):
        if price and photoname:
            Price.add(site=self, price=price)
            self.photo_path = photoname
            self.save()
            return True
        else:
            print(f'Цена - {price}  и фото - {photoname} '
                  'не были добавлены для сайта (id={id})')
            return False

    @classmethod
    def add_ref_link(cls, link):
        try:
            site = Site.objects.create(
                user=User.objects.get(username='admin'), url=link)
            return site.id
        except Exception as e:
            print('Добавление ссылки не удалось.' + str(e))
            return None

    @classmethod
    def delete_by_id(cls, id):
        try:
            count, obj_dict = Site.objects.filter(id=id).delete()
            return count > 0
        except Exception as e:
            print('Удаление ссылки не удалось.' + str(e))
            return None

    def run_task_for_price(self):
        pass


class Price(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    price = models.IntegerField()
    date = models.DateTimeField()

    @classmethod
    def add(cls, site, price):
        cls.objects.create(site=site, price=price, date=timezone.now())


# class RunningTask(models.Model):
#     site = models.OneToOneField(Site)
