from django.test import TestCase
from django.contrib.auth.models import User

from parsing.constants import DEFAULT_IMG_PATH
from .models import Site
from .parsers import Parsing, PhotoDownloader


# Create your tests here.
class TestParsing(TestCase):
    fixtures = []

    def setUp(self) -> None:
        self.site = Site.objects.create()

    def test_true(self):
        price, photo = Parsing(self.site.url).parse_data()
        self.assertIsNotNone(price)
        self.assertIsNotNone(photo)


class TestPhotoDownloader(TestCase):
    image_urls = dict(
        correct='https://img2.wbstatic.net/big/new/8660000/8661404-1.jpg',
        wrong='https://img2.wbstatic.net/big/new/8660000/agigdigdaggdg-1.jpg',
        unsupported_format=''
    )

    def test_correct_url(self):
        success, photo = PhotoDownloader(self.image_urls['correct']).download()
        self.assertTrue(success)
        self.assertNotEqual(photo, DEFAULT_IMG_PATH)

    def test_wrong_url(self):
        success, photo = PhotoDownloader(self.image_urls['wrong']).download()
        self.assertFalse(success)
        self.assertEqual(photo, DEFAULT_IMG_PATH)

    def test_empty_url(self):
        success, photo = PhotoDownloader('').download()
        self.assertFalse(success)
        self.assertEqual(photo, DEFAULT_IMG_PATH)
