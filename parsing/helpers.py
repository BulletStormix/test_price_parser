import time
from datetime import datetime

from . import models
from . import forms
from .constants import DEFAULT_IMG_PATH
from .parsers import Parsing


def get_sites_and_url_form():
    sites = models.Site.objects.all()
    for site in sites:
        last_price = site.last_price
        site.is_actual_price = datetime.date(last_price.date) == datetime.date(datetime.now()) if last_price else False
        site.price_rub = f'{last_price.price} руб.' if last_price else '-'
        site.photo_path = site.photo_path if site.photo_path else DEFAULT_IMG_PATH
    data = {'sites': sites, 'form': forms.LinkForm()}
    return data


def add_message_to_context(context, message=None):
    context['has_message'] = False if message is None else True
    if message:
        context['message'] = message
    return context


def add_link(url):
    site = models.Site.add_ref_link(url)
    if site:
        message = 'Ссылка успешно добавлена!'
    else:
        message = 'Ссылка не была добавлена из-за ошибки!'
    return bool(site), message


def delete_site(id):
    site = models.Site.delete_by_id(id)
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


def price_task(site_id):
    try:
        site = models.Site.objects.get(id=site_id)
    except models.Site.DoesNotExist:
        print(f'Сайт с id = {site_id} не существует!')
        return
    if site.is_running:
        print('Задача уже запущена!')
        return
    print('---------------------------------------------')
    print(f'Задача обновления данных сайта (id={site_id}) была запущена!')
    models.Site.objects.filter(id=site_id).update(is_running=True)
    try:
        price, photo_name = Parsing(site.url).parse_data()
        site.add_price_and_photo(price, photo_name)
    except Exception as e:
        print(f'Произошла ошибка при обновлении данных сайта (id={site_id}). {e}')
    finally:
        models.Site.objects.filter(id=site_id).update(is_running=False)
        print('---------------------------------------------')