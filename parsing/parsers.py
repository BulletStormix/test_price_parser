from time import sleep
import requests
import random

from abc import ABCMeta, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from .constants import PageParserEnum, GOODS_IMAGE_PATH, DEFAULT_IMG_PATH
from .constants import IdentifierEnum


class PageParser(metaclass=ABCMeta):
    site = None

    @staticmethod
    def get_parser(num):
        if num == PageParserEnum.Selenium:
            return SeleniumPageParser
        elif num == PageParserEnum.Requests:
            return RequestsPageParser

    @staticmethod
    def get_only_digits(string):
        return ''.join([c for c in string if c.isdigit()])

    @abstractmethod
    def open(self):
        pass

    def close(self):
        self.site.parser = None
        self.site = None

    def get_element_on_page(self, elem_src):
        pass

    def try_get_element_on_page(self, elem_src):
        try:
            elem = self.get_element_on_page(elem_src)
            return elem
        except Exception as e:
            print('Не удалось найти элемент на странице (type={0},id={1})'.format(elem_src.type, elem_src.id))
            return None

    def get_page_elem(self, elem_src):
        if not isinstance(elem_src, list):
            return self.try_get_element_on_page(elem_src)
        else:
            for el_src in elem_src:
                elem = self.try_get_element_on_page(el_src)
                if elem:
                    return elem
            return None

    # Декоратор для открытия парсера
    @staticmethod
    def decorator_open(function):
        def fun(self):
            for i in range(2):
                try:
                    function(self)
                    break
                except:
                    print('Произошла ошибка при открытии сайта!')
        return fun


class RequestsPageParser(PageParser):
    site = None
    driver = None

    def __init__(self, site):
        self.site = site

    @staticmethod
    def return_bs(url):
        response = requests.get(url)
        return BeautifulSoup(response.text, "html.parser")

    @PageParser.decorator_open
    def open(self):
        print(f'Открытие сайта {self.site.url}')
        self.response = requests.get(self.site.url)
        self.bs = BeautifulSoup(self.response.text, "html.parser")


class SeleniumPageParser(PageParser):
    site = None
    driver = None

    def __init__(self, *args):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1366x768")
        self.driver = webdriver.Chrome(executable_path=r'C:\chromedriver.exe', options=chrome_options)
        # self.driver = webdriver.Chrome(r'C:\chromedriver.exe')
        if args:
            self.site = args[0]

    def set_site(self, site):
        self.site = site

    @PageParser.decorator_open
    def open(self):
        print(f'Открытие сайта {self.site.url}')
        self.driver.get(self.site.url)

    def close(self):
        print('Закрытие сайта')
        self.driver.close()
        super(SeleniumPageParser, self).close()

    def get_element_on_page(self, elem_src):
        func = {
            IdentifierEnum.id: self.driver.find_element_by_id,
            IdentifierEnum.class_: self.driver.find_elements_by_class_name,
            IdentifierEnum.xpath: self.driver.find_element_by_xpath
        }[elem_src.type]
        return func(elem_src.id)

    def get_elem_by_tag(self, where, tag):
        return where.find_element_by_tag_name(tag)

    @property
    def price_elem(self):
        return self.get_page_elem(self.site.price_src)

    @property
    def photo_elem(self):
        return self.get_page_elem(self.site.photo_src)

    def get_photo_elem_attr(self, attr):
        elem = self.get_page_elem(self.site.photo_src)
        return elem.get_attribute(attr)


class PhotoDownloader:
    """Класс, отвечающий за загрузку изображения по ссылке"""

    photo_url = None

    def __init__(self, url=None):
        self.photo_url = url

    @staticmethod
    def get_file_format(url):
        formats = ['jpg', 'png', 'jpeg']
        url = urlparse(url).path
        for f in formats:
            if url.endswith(f):
                return f
        return None

    @staticmethod
    def get_file_name(self, img_format):
        return GOODS_IMAGE_PATH + f'img_{random.randint(100, 10 ** 6)}.{img_format}'

    def _download(self):
        """Загружает изображение по ссылке и возвращает 2 значения:
        признак успешного завершения и путь до файла, если не было ошибок"""

        try:
            img = requests.get(self.photo_url)
            image_format = self.get_file_format(self.photo_url)
            if image_format is None:
                return DEFAULT_IMG_PATH
            file_name = self.get_file_name(image_format)
            with open(file_name, "wb") as out:
                out.write(img.content)
            return True, file_name
        except Exception as e:
            print(f'Произошла ошибка при загрузке и сохранении картинки: {e}')
            return False, None

    def download(self):
        success, file_name = self._download()
        photo_path = file_name if success else DEFAULT_IMG_PATH
        return photo_path
