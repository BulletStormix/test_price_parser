from urllib.parse import urlparse
from abc import ABCMeta, abstractmethod

from .constants import IdentifierEnum,TypeAndId, PageParserEnum


def get_only_digits(string):
    return ''.join([c for c in string if c.isdigit()])


class SiteParsing(metaclass=ABCMeta):
    #TODO: сделать загрузку полей из отдельного файла конфига или из бд
    main_url = None
    page_parser_type = None
    price_src = None
    photo_src = None

    @staticmethod
    def get_site(url):
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
        # TODO: добавить проверку, что у сайта добавлены все поля

    @abstractmethod
    def process_price_element(self, element):
        pass

    @abstractmethod
    def process_photo_element(self, element):
        pass


class Wildberries(SiteParsing):
    main_url = 'https://www.wildberries.ru/'
    page_parser_type = PageParserEnum.Selenium
    price_src = TypeAndId(IdentifierEnum.class_, 'final-cost')
    photo_src = TypeAndId(IdentifierEnum.xpath, '//*[@id="Azoom"]')

    def process_price_element(self, element):
        price_elem = element[0]
        return get_only_digits(price_elem.text)

    def process_photo_element(self, element):
        from parsing.parsers import PhotoDownloader
        photo_url = element.get_attribute('href')
        return PhotoDownloader(photo_url).download()[1]


class Lamoda(SiteParsing):
    main_url = 'https://www.lamoda.ru/'
    page_parser_type = PageParserEnum.Selenium
    price_src = [
        TypeAndId(IdentifierEnum.class_, 'ii-product__price-current_red'),
        TypeAndId(IdentifierEnum.class_, 'ii-product__price-discount_second'),
        TypeAndId(IdentifierEnum.class_, 'ii-product__price-discount_first')
    ]
    photo_src = TypeAndId(IdentifierEnum.class_, 'gallery-image')

    def process_price_element(self, element):
        price_elem = element[0]
        return get_only_digits(price_elem.text)

    def process_photo_element(self, element):
        # TODO: исправить зависимости от парсера
        from parsing.parsers import PhotoDownloader
        photo_elem = element[0]
        photo_url = photo_elem.get_attribute('src')
        return PhotoDownloader(photo_url).download()[1]


all_sites = [
    Wildberries, Lamoda
]
