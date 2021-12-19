from datetime import datetime, timedelta
from os import getenv

import requests
from cdek.api import CDEKClient
from pochta import tracking


def pochta_delivery(to_index: int, weight=None, price=None, from_index=125476) -> str:
    url_base = 'https://delivery.pochta.ru/v2/calculate'
    if weight and price:
        # расчет тарифа и контрольные сроки
        url_base += '/tariff/'
        pack = 40 if int(weight) > 2000 else 20 if 1000 < int(weight) <= 2000 else 10  # s-10, m-20, l-30, xl-40
        params = {'object': '4040', 'weight': weight, 'pack': pack,
                  'sumoc': f'{price}00'}
    else:
        # только сроки доставки
        params = {'object': '27040', 'weight': '1000', 'pack': '20'}

    params['from'], params['to'] = from_index, to_index
    params['date'] = f'&date={(datetime.now() + timedelta(days=2 if not price else 3)).strftime("%Y%m%d")}'

    resp = requests.get(url_base + '/delivery?json', params=params)
    resp_json = resp.json()

    try:
        delivery_days = resp_json["delivery"]["max"]
        delivery_deadline = datetime.strptime(resp_json["delivery"]["deadline"][0:8], "%Y%m%d").strftime("%d.%m.%Y")
        delivery_days_str = f'Срок доставки:  <b>{delivery_days}</b> дн.\nДоставка:  до <b>{delivery_deadline}</b>'
        if price:
            pay_nds = resp_json["paynds"]
            return f'Стоимость:  <b>{float(pay_nds / 100):5.2f}</b> руб. \n' + delivery_days_str
        else:
            return delivery_days_str

    except KeyError:
        return resp_json['errors'][0]['msg']


def pochta_parcel_tracking(track_number: str) -> str:
    pochta_login = getenv('POCHTA_LOGIN')
    pochta_password = getenv('POCHTA_PASSWORD')
    try:
        data = []
        resp = tracking.SingleTracker(pochta_login, pochta_password).get_history(track_number)
        for j in resp:
            data.append(f"{(j['OperationParameters']['OperDate']).strftime('%d.%m.%Y-%H:%M:%S')} -"
                        f"{j['OperationParameters']['OperType']['Name']}" +
                        f" - {j['OperationParameters']['OperAttr']['Name']}"
                        if j['OperationParameters']['OperAttr']['Name'] else '')
        return '\n'.join(data if len(data) <= 14 else data[-10:])
    except TypeError:
        return 'По данному треку информация недоступна'


def cdek_parcel_tracking(track_number: str) -> str:
    cdek_id = getenv('CDEK_ID')
    cdek_pass = getenv('CDEK_PASS')
    client = CDEKClient(cdek_id, cdek_pass)
    order_info = client.get_orders_statuses([int(track_number)], show_history=1)[0]
    try:
        data = []
        for i in order_info['Status']['State']:
            if i['CityName'] == 'Управляющая Компания':
                continue
            else:
                date = datetime.fromisoformat(i['Date']).strftime('%d.%m.%Y-%H:%M:%S')
                data.append(f"{date} - {i['CityName']} - {i['Description']}")
        return '\n'.join(data if len(data) <= 14 else data[-10:])
    except KeyError:
        return 'Не найден трек номер'
