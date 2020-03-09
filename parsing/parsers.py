import os
import requests
import random
from time import sleep

from abc import ABCMeta, abstractmethod
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver import ChromeOptions
from selenium.webdriver.remote.webelement import WebElement
from urllib.parse import urlparse

from config.settings import ADDITIONAL_FILES_DIR
from parsing.exceptions import *
from parsing.settings import GOODS_IMAGE_PATH
from parsing.site_config import all_sites_config, SiteConfigException
from .constants import (
    IdentifierEnum, PageParserEnum, SeleniumSettings, TypeAndId)


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
    # Элемент, с которого начинается поиск
    where = None

    @staticmethod
    def get_parser(parser_type, url):
        """Получение экземпляра парсера"""
        assert parser_type is not None, f'Некорретный тип парсера - {parser_type}'
        assert url, f'Задана некорретная ссылка на сайт - {url}'

        parser_class = {
            PageParserEnum.Selenium: SeleniumPageParser,
            PageParserEnum.Requests: RequestsPageParser
        }.get(parser_type)

        if not parser_class:
            raise IncorrectParserType()

        return parser_class(url)

    def try_get_element_on_page(self, elem_src):
        """Безопасное получение элемента на странице
        Не требует переопределения"""

        try:
            elem = self.get_element_on_page(elem_src)
            return elem
        except ElementNotFoundedOnPage(elem_src) as e:
            print(e.message)
            return None

    def get_page_elem(self, elem_src):
        """Расширенная обработка элемента. Позволяет задавать несколько типов
        идентификаторов, будет выбран первый ненулевой результат.
        Не требует переопределения
        :param elem_src: Тип и сам идентификатор
        :type elem_src: TypeAndId
        :raise: ElementNotFoundedOnPage
        """

        if not isinstance(elem_src, list):
            return self.get_element_on_page(elem_src)
        else:
            for el_src in elem_src:
                elem = self.try_get_element_on_page(el_src)
                if elem:
                    return elem
            raise ElementNotFoundedOnPage()

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def get_element_on_page(self, elem_src):
        pass

    def reset_where_to_find(self):
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
            Chrome: SeleniumSettings(
                webdriver_class=webdriver.Chrome,
                option_class=ChromeOptions,
                path=r'{}'.format(
                    os.path.join(ADDITIONAL_FILES_DIR, 'chromedriver.exe'))
            ),
            Firefox: SeleniumSettings(
                webdriver_class=webdriver.Firefox,
                option_class=FirefoxOptions,
                path=r'{}'.format(
                    os.path.join(ADDITIONAL_FILES_DIR, 'geckodriver.exe'))
            )
        }

    url = None
    invisible = False
    program = SeleniumProgram.Firefox

    @classmethod
    def get_webdriver(cls):
        setting = cls.SeleniumProgram.settings[cls.program]
        if cls.invisible:
            driver_options = setting.option_class()
            driver_options.add_argument("--headless")
            driver_options.add_argument("--window-size=1366x768")
            driver = setting.webdriver_class(
                executable_path=setting.path, options=driver_options)
        else:
            driver = setting.webdriver_class(executable_path=setting.path)
        return driver

    def __init__(self, url):
        self.url = url
        self.driver = self.get_webdriver()
        self.setting = self.SeleniumProgram.settings[self.program]
        self.reset_where_to_find()

    @open_parser
    def open(self):
        print(f'Открытие сайта {self.url}')
        self.driver.get(self.url)

    def close(self):
        print('Закрытие сайта')
        self.driver.close()

    def reset_where_to_find(self):
        self.where = self.driver

    @staticmethod
    def get_num_of_list(elem_list, num):
        """Возвращается num-ый по счёту элемент массива"""
        assert isinstance(elem_list, list)

        if 0 <= num <= len(elem_list):
            try:
                return elem_list[num]
            except IndexError as e:
                print('Индекс вышел за границы массива!')

        return None

    def get_supported_identifiers(self):
        """Возвращает словарь поддерживаемых идентификторов и соответствующих
        им функций для текущего расположения веб-драйвера
        """
        identifier_functions = {}
        is_web_element = isinstance(self.where, WebElement)

        if (isinstance(self.where, self.setting.webdriver_class) or
                is_web_element):
            identifier_functions.update({
                IdentifierEnum.id: self.where.find_element_by_id,
                IdentifierEnum.class_: self.where.find_elements_by_class_name,
                IdentifierEnum.xpath: self.where.find_element_by_xpath,
                IdentifierEnum.tag: self.where.find_element_by_tag_name
            })
        if is_web_element:
            identifier_functions[IdentifierEnum.attr] = self.where.get_attribute
            identifier_functions[IdentifierEnum.text] = getattr
        if isinstance(self.where, list):
            identifier_functions[IdentifierEnum.num] = self.get_num_of_list
        return identifier_functions

    def get_param_for_identifier_function(self, function, elem_src):
        """Возвращает словарь параметров для передачи в функцию
        получения идентификатора
        :param elem_src: Тип идентификатора и сам идентификатор
        :type elem_src: TypeAndId
        :param elem_src: Функция для получения идентификатора
        :return args, kwargs: Неименованные/именованные аргументы для функции
        :raise SiteConfigException
        """
        args = []
        kwargs = {}
        if isinstance(self.where, list):
            try:
                kwargs['elem_list'] = self.where
                kwargs['num'] = int(elem_src.id)
            except ValueError:
                raise SiteConfigException('Некорректный параметр!')
        elif function == getattr and elem_src.type == IdentifierEnum.text:
            args = [self.where, 'text', None]
        else:
            # По умолчанию
            args = [elem_src.id]
        return args, kwargs

    def get_element_on_page(self, elem_src):
        """ Получение элемента на странице согласно идентификатору
        :param elem_src: Тип идентификатора и сам идентификатор
        :type elem_src: TypeAndId
        :raise: WrongIdentifier, ElementNotFoundedOnPage
        """

        identifier_functions = self.get_supported_identifiers()
        function = identifier_functions.get(elem_src.type)
        if not function:
            raise ElementNotFoundedOnPage(elem_src)

        args, kwargs = self.get_param_for_identifier_function(
            function, elem_src)
        print(f'Function={function}, id={elem_src.id}', end='')
        result = function(*args, **kwargs)
        print(f', result={result}')
        if not result:
            raise ElementNotFoundedOnPage()

        self.where = result
        return result


class Parsing:
    """Основной класс, соединяющий парсеры с сайтами"""

    def __init__(self, url):
        self.url = url
        self.site_config = self.get_site_config()
        self.parser = PageParser.get_parser(
            self.site_config.parser_type, url)

    def get_site_config(self):
        base_url = urlparse(self.url).netloc
        for site in all_sites_config:
            if base_url == urlparse(site.base_url).netloc:
                return site
        raise UnsupportedSiteUrl(base_url)

    def parse_data(self):
        # TODO: проверить соединение с сайтом,
        # только после этого приступать к парсингу (это также удостовериться, что ссылка правильная)
        self.parser.open()
        site = self.site_config
        price = self.process_price(site.price_src)
        photo_name = self.process_photo(site.photo_src)
        self.parser.close()
        return price, photo_name

    def process_element(self, source):
        self.parser.reset_where_to_find()
        for elem_source in source:
            element = self.parser.get_page_elem(elem_source)
            if not element:
                raise ElementNotFoundedOnPage('Элемент не найден на странице!')
        return element

    def process_price(self, source):
        element = self.process_element(source)
        return ''.join([c for c in element if c.isdigit()])

    def process_photo(self, source):
        element = self.process_element(source)
        success, photo_path, _ = PhotoDownloader(element).download()
        return photo_path


class PhotoDownloader:
    """Класс, отвечающий за загрузку изображения по ссылке"""

    photo_url = None
    supported_formats = ['jpg', 'png', 'jpeg']

    def __init__(self, url=None):
        self.photo_url = url

    def get_file_format(self):
        """Получает расширение файла изображения для дальнейшей обработки
        :raise: FileNotDownloaded, UnsupportedFileFormat
        """
        url_path = urlparse(self.photo_url).path.lower()
        if not url_path:
            raise FileNotDownloaded(self.photo_url)
        for f in self.supported_formats:
            if url_path.endswith(f):
                return f
        raise UnsupportedFileFormat(url_path)

    @staticmethod
    def generate_file_name(img_format):
        """Генерирует имя файла изображения, проверяет, что имя уникально
        :param img_format: Расширение файла изображения
        """
        is_unique = False
        file_name = None
        while not is_unique:
            random_num = random.randint(100, 10 ** 6)
            file_name = os.path.join(
                GOODS_IMAGE_PATH, f'img_{random_num}.{img_format}')
            is_unique = not os.path.exists(file_name)
        return file_name

    def get_file_name(self):
        """Определяет формат изображения и возвращает путь к новому файлу"""
        image_format = self.get_file_format()
        file_name = self.generate_file_name(image_format)
        return file_name

    def _download(self):
        """Загружает изображение по ссылке и возвращает 2 значения:
        признак успешного завершения и путь до файла, если не было ошибок
        :raise: FileNotDownloaded"""

        img = requests.get(self.photo_url)
        if (img.status_code != 200 or not img.content or
                not img.headers['Content-Type'].startswith('image')):
            raise FileNotDownloaded(self.photo_url)
        file_name = self.get_file_name()
        try:
            with open(file_name, "wb") as out:
                out.write(img.content)
            return True, file_name
        except Exception as e:
            print(f'Произошла ошибка при сохранении картинки: {e}')
            return False, None

    def download(self):
        """Скачивает изображение по ссылке и возвращает признак успешности
        завершения операции и путь до файла (если возникли ошибки то путь до
        до дефолтного изображения), а также сообщение об ошибке (если есть)
        """
        success = False
        file_name = None
        error = ''

        try:
            if not self.photo_url:
                raise FileNotDownloaded()
            success, file_name = self._download()
        except (PhotoDownloaderException, requests.RequestException) as e:
            error = e

        photo_path = file_name if success else None
        return success, photo_path, error
