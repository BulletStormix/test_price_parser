import os

from django.core.exceptions import ImproperlyConfigured

from config.settings import BASE_DIR


# Расположение конфигураций сайтов
SITE_CONFIG_PATH = os.getenv('SITE_CONFIG_PATH')
if not SITE_CONFIG_PATH or not os.path.exists(SITE_CONFIG_PATH):
    # Дефолтное расположение файла конфиграций сайтов
    SITE_CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'site_config.txt')
    if not os.path.exists(SITE_CONFIG_PATH):
        raise ImproperlyConfigured(
            'Некорректно задан путь до конфигураций сайтов SITE_CONFIG_PATH!')