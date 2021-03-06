import os
from collections import namedtuple

from config.settings import GOODS_IMAGE_PATH

PRICE_NOT_FOUNDED = 'Цена не найдена'
DEFAULT_IMG_PATH = os.path.join(GOODS_IMAGE_PATH, 'default.jpg')
link_to_index_page = "<a href='/'>Вернуться на главную страницу</a>"


class BaseEnumerate:
    values = {}

    @classmethod
    def get_choices(cls):
        return [(value, key) for key, value in cls.values.items()]


class IdentifierEnum(BaseEnumerate):
    id = 0
    class_ = 1
    xpath = 2
    tag = 3

    values = {
        'id': id,
        'class_': class_,
        'xpath': xpath,
        'tag': tag,
    }


class PageParserEnum(BaseEnumerate):
    Selenium = 0
    Requests = 1

    values = {
        'Selenium': Selenium,
        'Requests': Requests,
    }


TypeAndId = namedtuple('TypeAndId', ['type', 'id'])
