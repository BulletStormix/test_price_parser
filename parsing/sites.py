from urllib.parse import urlparse
from abc import ABCMeta, abstractmethod
from cached_property import cached_property

from parsing.constants import TypeAndId
from parsing.constants import PageParserEnum
from parsing.constants import IdentifierEnum
from parsing.parsers import *


class SiteParsing:
    main_url = None
    page_parser_type = None
    price_src = None
    photo_src = None

    @staticmethod
    def get_site(url, *args):
        base_url = urlparse(url).netloc
        for site in all_sites:
            if base_url == urlparse(site.main_url).netloc:
                return site(url)

    def set_url(self, url):
        self.url = url
        self.url_obj = urlparse(self.url)
        self.base_url = self.url_obj.netloc

    def __init__(self, url):
        self.set_url(url)
        ParserClass = PageParser.get_parser(self.page_parser_type)
        self.parser = ParserClass(self)
        self.parse_data()

    def parse_data(self):
        # TODO: проверить соединение с сайтом,
        # только после этого приступать к парсингу (это также удостоверит, что ссылка правильная)
        self.parser.open()
        data = self.price, self.photo_name
        # Завершение работы и обнуление ссылок (для очистки мусора)
        self.parser.close()
        return data

    @cached_property
    def price(self):
        price_elem = self.parser.price_elem
        price = self.parser.get_only_digits(price_elem.text)
        return price

    def photo_name(self):
        pass


class Wildberries(SiteParsing):
    main_url = 'https://www.wildberries.ru/'
    page_parser_type = PageParserEnum.Selenium
    price_src = TypeAndId(IdentifierEnum.class_, 'final-cost')
    photo_src = TypeAndId(IdentifierEnum.xpath, '//*[@id="Azoom"]')

    @cached_property
    def price(self):
        price_elem = self.parser.price_elem[0]
        return self.parser.get_only_digits(price_elem.text)

    @cached_property
    def photo_name(self):
        photo_elem = self.parser.photo_elem
        photo_url = photo_elem.get_attribute('href')
        return PhotoDownloader(photo_url).download()


class Lamoda(SiteParsing):
    main_url = 'https://www.lamoda.ru/'
    page_parser_type = PageParserEnum.Selenium
    price_src = [
        TypeAndId(IdentifierEnum.class_, 'ii-product__price-current_red'),
        TypeAndId(IdentifierEnum.class_, 'ii-product__price-discount_second'),
        TypeAndId(IdentifierEnum.class_, 'ii-product__price-discount_first')
    ]
    photo_src = TypeAndId(IdentifierEnum.class_, 'gallery-slide')

    @cached_property
    def price(self):
        price_elem = self.parser.price_elem
        if not price_elem:
            return None
        price_elem = price_elem[0]
        return self.parser.get_only_digits(price_elem.text)

    @cached_property
    def photo_name(self):
        photo_elem = self.parser.photo_elem[0]
        photo_elem = self.parser.get_elem_by_tag(photo_elem, 'img')
        photo_url = photo_elem.get_attribute('src')
        return PhotoDownloader(photo_url).download()


all_sites = [
    Wildberries, Lamoda
]
