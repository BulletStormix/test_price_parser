from django.test import TestCase
from django.contrib.auth.models import User

from .models import Site
from .parsers import Parsing

# Create your tests here.
class TestParsing(TestCase):
    fixtures = []

    def setUp(self) -> None:
        self.site = Site.objects.create()

    def test_true(self):
        price, photo = Parsing(self.site.url).parse_data()
        self.assertIsNotNone(price)
        self.assertIsNotNone(photo)
