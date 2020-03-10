import time
from datetime import datetime

from django.db import transaction

from parsing.parsers import Parsing
from .settings import DEFAULT_IMG_PATH
from .forms import LinkForm
from .models import Site, RunningTask


def get_sites_and_url_form():
    sites = Site.objects.all()
    for site in sites:
        last_price = site.last_price
        is_today_date = last_price.date.date() == datetime.now().date()
        site.is_running = site.task_is_running
        site.is_actual_price = is_today_date if last_price else False
        site.price_rub = f'{last_price.price} руб.' if last_price else '-'
        site.photo_path = site.photo_path if site.photo_path else DEFAULT_IMG_PATH
    data = {'sites': sites, 'form': LinkForm()}
    return data


def add_message_to_context(context, message=None):
    context['has_message'] = False if message is None else True
    if message:
        context['message'] = message
    return context


def add_link(url):
    site = Site.add_ref_link(url)
    if site:
        message = 'Ссылка успешно добавлена!'
    else:
        message = 'Ссылка не была добавлена из-за ошибки!'
    return bool(site), message


def delete_site(id):
    site = Site.delete_by_id(id)
    if site:
        message = 'Ссылка успешно удалена!'
    else:
        message = 'Ссылка не была удалена из-за ошибки!'
    return message


def calculate_time(fun):
    def calculate(url_param):
        t = time.time()
        result = fun(url_param)
        print(f'Время на обработку запроса - {time.time() - t} секунд')
        return result
    return calculate


class SiteTaskContextManager:
    """Менеджер контекста для создания задач обновления данных сайтов
     и для вывода информации при запуске и завершении задач"""
    def __init__(self, site):
        self.site = site

    def __enter__(self):
        print('---------------------------------------------')
        print(f'Задача обновления данных сайта '
              f'(id={self.site.id}) была запущена!')
        RunningTask.create_task_for_site(self.site)

    def __exit__(self, exc_type, exc_val, exc_tb):
        RunningTask.delete_task_for_site(self.site)
        print('---------------------------------------------')


@transaction.atomic
def run_price_task(site_id):
    """Запускает задачу по обновлению цены и фото для сайта"""

    try:
        site = Site.objects.get(id=site_id)
    except Site.DoesNotExist:
        print(f'Сайт с id = {site_id} не существует!')
        return

    if site.task_is_running:
        print('Задача для сайта с id = {site_id} уже запущена!')
        return

    with SiteTaskContextManager(site=site):
        price, photo_name = Parsing(site.url).parse_data()
        print(f'Price - {price}; Photo - {photo_name}')
        site.add_price_and_photo(price, photo_name)
