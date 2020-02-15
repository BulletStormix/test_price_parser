import os
import requests
import random
from time import sleep

from abc import ABCMeta, abstractmethod
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from urllib.parse import urlparse

from config.settings import ADDITIONAL_FILES_DIR
from .sites import SiteParsing
from .constants import IdentifierEnum, PageParserEnum, GOODS_IMAGE_PATH, DEFAULT_IMG_PATH


def open_parser(function):
    """Декоратор для открытия парсера с возможностью повторной попытки"""
    def fun(self):
        for i in range(2):
            try:
                function(self)
                break
            except:
                print('Произошла ошибка при открытии сайта!')
            sleep(1)
    return fun


class PageParser(metaclass=ABCMeta):
    url = None

    @staticmethod
    def get_parser(parser_type, url):
        parser_class = {
            PageParserEnum.Selenium: SeleniumPageParser,
            PageParserEnum.Requests: RequestsPageParser
        }[parser_type]
        return parser_class(url)

    def try_get_element_on_page(self, elem_src):
        """Безопасное получение элемента на странице
        Не требует переопределения"""

        try:
            elem = self.get_element_on_page(elem_src)
            return elem
        except Exception as e:
            print(f'Не удалось найти элемент на странице '
                  f'(type={elem_src.type}, id={elem_src.id})')
            return None

    def get_page_elem(self, elem_src):
        """Расширенная обработка элемента. Позволяет задавать несколько типов
        идентификаторов, будет выбран первый ненулевой результат.
        Не требует переопределения"""

        if not isinstance(elem_src, list):
            return self.try_get_element_on_page(elem_src)
        else:
            for el_src in elem_src:
                elem = self.try_get_element_on_page(el_src)
                if elem:
                    return elem
            return None

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def get_element_on_page(self, elem_src):
        pass

    def close(self):
        pass


class RequestsPageParser(PageParser):
    url = None

    def __init__(self, url):
        self.url = url

    @staticmethod
    def return_bs(url):
        response = requests.get(url)
        return BeautifulSoup(response.text, "html.parser")

    @open_parser
    def open(self):
        print(f'Открытие сайта {self.url}')
        self.response = requests.get(self.url)
        self.bs = BeautifulSoup(self.response.text, "html.parser")

    def get_element_on_page(self, elem_src):
        # TODO: доработать функционал
        raise NotImplementedError()


class SeleniumPageParser(PageParser):
    class SeleniumProgram:
        Chrome = 0
        Firefox = 1

        settings = {
            Chrome: dict(
                webdriver_class=webdriver.Chrome,
                option_class=ChromeOptions,
                path=r'{}'.format(os.path.join(ADDITIONAL_FILES_DIR,
                                               'chromedriver.exe'))
            ),
            Firefox: dict(
                webdriver_class=webdriver.Firefox,
                option_class=FirefoxOptions,
                path=r'{}'.format(os.path.join(ADDITIONAL_FILES_DIR,
                                               'geckodriver.exe'))
            )
        }

    url = None
    invisible = False
    program = SeleniumProgram.Firefox

    @classmethod
    def get_webdriver(cls):
        setting = cls.SeleniumProgram.settings[cls.program]
        if cls.invisible:
            driver_options = setting['option_class']()
            driver_options.add_argument("--headless")
            driver_options.add_argument("--window-size=1366x768")
            driver = setting['webdriver_class'](
                executable_path=setting['path'], options=driver_options)
        else:
            driver = setting['webdriver_class'](executable_path=setting['path'])
        return driver

    def __init__(self, url):
        self.url = url
        self.driver = self.get_webdriver()

    @open_parser
    def open(self):
        print(f'Открытие сайта {self.url}')
        self.driver.get(self.url)

    def close(self):
        print('Закрытие сайта')
        self.driver.close()

    def get_element_on_page(self, elem_src, where=None):
        """ Получение элемента на странице согласно идентификатору
        :param elem_src: Тип идентификатора и сам идентификатор
        :type elem_src: TypeAndId
        :param where: Элемент, с которого начинается поиск
        """
        where = self.driver if not where else where
        func = {
            IdentifierEnum.id: where.find_element_by_id,
            IdentifierEnum.class_: where.find_elements_by_class_name,
            IdentifierEnum.xpath: where.find_element_by_xpath,
            IdentifierEnum.tag: where.find_element_by_tag_name
        }[elem_src.type]
        return func(elem_src.id)

    # TODO: переделать под обычный атрибут
    def get_attr(self, attr):
        return self.driver.get_attribute(attr)


class Parsing:
    """Основной класс, соединяющий парсеры с сайтами"""

    def __init__(self, url):
        self.site = SiteParsing.get_site(url)
        self.parser = PageParser.get_parser(self.site.page_parser_type, url)

    def parse_data(self):
        # TODO: проверить соединение с сайтом,
        # только после этого приступать к парсингу (это также удостовериться, что ссылка правильная)
        self.parser.open()
        site = self.site
        price = self.process_element(
            site.price_src, site.process_price_element)
        photo_name = self.process_element(
            site.photo_src, site.process_photo_element)
        self.parser.close()
        return price, photo_name

    def process_element(self, elem_source, processing_func):
        element = self.parser.get_page_elem(elem_source)
        if not element:
            return None
        return processing_func(element)


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
    def get_file_name(img_format):
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
        if self.photo_url is None:
            print('Нет ссылки на изображение. Изображение не будет загружено!')
            return None
        success, file_name = self._download()
        photo_path = file_name if success else DEFAULT_IMG_PATH
        return photo_path
