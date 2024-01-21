import requests
import json
from odoo import _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError


def get_access_token_ahamove(aha_id):
    if aha_id.active:
        return aha_id.access_token

    company_id = aha_id.company_id
    api_key = aha_id.secret_key
    params = {
        'name': company_id.name,
        'mobile': company_id.phone,
        'api_key': api_key,
        'address': company_id.street
    }
    path_url = '/v1/partner/register_account'
    url_aha = aha_id.url
    url = url_aha + path_url
    response = requests.get(url, params=params, headers={
        'Cache-Control': 'no-cache',
    })
    if response.status_code == 200:
        response = response.json()
        aha_id.access_token = response.get('token')
        return aha_id.access_token
    return False


def get_api_service_type_ahamove(lat, lng, aha_id):
    path_url = '/v1/order/service_types'
    url = aha_id.url + path_url
    response = requests.get(url, params={'lat': lat, 'lng': lng},
                            headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        raise UserError(_('Không thể lấy được danh sách dịch vụ ahamove. Kết nối thất bại!'))
        return False
    elif response.status_code == 200:
        response = response.json()
        return response[0].get('city_id')


def get_api_fee_order_ahahmove(delivery_id, aha_id):
    token = get_access_token_ahamove(aha_id)
    city_id = get_api_service_type_ahamove(delivery_id.lat_sender, delivery_id.long_sender, aha_id)
    if not city_id:
        delivery_id.failed_reason = _('Không thể lấy được danh sách dịch vụ ahamove. Kết nối thất bại!')
        return False
    service_id = city_id + '-BIKE'
    special_service = city_id + '-BIKE-THERMALBAG'
    path = [
        {
            'lat': float(delivery_id.lat_sender),
            'lng': float(delivery_id.long_sender),
            'address': delivery_id.address_sender,
        },
        {
            'lat': float(delivery_id.lat_recipient),
            'lng': float(delivery_id.long_recipient),
            'address': delivery_id.address_recipient,
        }
    ]
    requests_service = [
        {'_id': special_service}
    ]
    PARAMS = {'order_time': 0, 'service_id': service_id, 'token': token, 'path': json.dumps(path),
              'requests': json.dumps(requests_service),
              'suggest_promotion': True}
    path_url = '/v1/order/estimated_fee'
    url_aha = aha_id.url
    url = url_aha + path_url
    response = requests.get(url,
                            params=PARAMS)
    if response.status_code == 200:
        response = response.json()
        fee = response.get('total_price')
        return fee
    elif response.status_code == 404:
        raise UserError(_('Đã xảy ra lỗi với đơn vị Ahamove%s') % response.text)
    else:
        return False


def create_order_ahamove(delivery_id):
    token = get_access_token_ahamove(delivery_id.delivery_partner_id)
    city_id = get_api_service_type_ahamove(delivery_id.lat_sender, delivery_id.long_sender,
                                           delivery_id.delivery_partner_id)
    if not city_id:
        return False
    service_id = city_id + '-BIKE'
    special_service = city_id + '-BIKE-THERMALBAG'
    path = [
        {
            'lat': float(delivery_id.lat_sender),
            'lng': float(delivery_id.long_sender),
            'address': delivery_id.address_sender,
            'mobile': delivery_id.phone_sender,
            'name': delivery_id.sender_id.name,
            'remarks': 'call me',
        },
        {
            'lat': float(delivery_id.lat_recipient),
            'lng': float(delivery_id.long_recipient),
            'address': delivery_id.address_recipient,
            'mobile': delivery_id.phone_recipient,
            'name': delivery_id.recipient_id,
            'cod': int(delivery_id.cod)
        }
    ]
    requests_service = [
        {'_id': special_service}
    ]
    PARAMS = {
        'order_time': 0,
        'service_id': service_id,
        'requests': json.dumps(requests_service),
        'token': token,
        'path': json.dumps(path),
        'payment_method': 'BALANCE',
        'idle_until': 0,
        'remarks': delivery_id.description,
        'suggest_promotion': True
    }
    path_url = '/v1/order/create'
    url_aha = delivery_id.delivery_partner_id.url
    url = url_aha + path_url
    response = requests.get(url, params=PARAMS)
    if response.status_code == 200:
        return response.json()
    else:
        raise UserError(
            _('Không thể tạo đơn giao vận trên Ahamove. Kết nối thất bại! Mã lỗi %s') % response.text)


def get_order_detail(delivery_id):
    token = get_access_token_ahamove(delivery_id.delivery_partner_id)
    params = {
        'token': token,
        'order_id': delivery_id.delivery_reference
    }
    token = 'token=' + token
    order_id = 'order_id=' + delivery_id.delivery_reference
    path_url = '/v1/order/detail'
    url_aha = delivery_id.delivery_partner_id.url
    url = url_aha + path_url + '?' + token + '&' + order_id
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise UserError(_('Something went wrong while taking order details'))


def cancel_order_api_ahamove(delivery_id):
    token = get_access_token_ahamove(delivery_id.delivery_partner_id)
    order_id = delivery_id.delivery_reference
    comment = 'Thay đổi đơn hàng'
    PARAMS = {
        'order_id': order_id,
        'comment': comment,
        'token': token,
    }
    path_url = '/v1/order/cancel'
    url_aha = delivery_id.delivery_partner_id.url
    url = url_aha + path_url
    response = requests.get(url, params=PARAMS)
    if response.status_code == 200:
        return True
    else:
        raise UserError(
            _('Không thể hủy đơn giao vận trên Ahamove. Kết nối thất bại!'))
