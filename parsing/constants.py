from enum import Enum
from collections import namedtuple


PRICE_NOT_FOUNDED = 'Цена не найдена'
GOODS_IMAGE_PATH = 'static/goods_images/'
DEFAULT_IMG_PATH = GOODS_IMAGE_PATH + 'default.jpg'
link_to_index_page = "<a href='/'>Вернуться на главную страницу</a>"

class BaseEnumerate:
    values = {}

    @classmethod
    def get_choices(cls):
        return [(value, key) for key, value in cls.values.items()]


class IdentifierEnum(Enum):
    id = 0
    class_ = 1
    xpath = 2
    tag = 3


class PageParserEnum(Enum):
    Selenium = 0
    Requests = 1


TypeAndId = namedtuple('TypeAndId', ['type', 'id'])


class Identifier(BaseEnumerate):
    values = {
        'id': 0,
        'class': 1,
        'xpath': 2,
        'tag': 3,
    }


class PageParser(BaseEnumerate):
    values = {
        'Selenium': 0,
        'Requests': 1
    }
