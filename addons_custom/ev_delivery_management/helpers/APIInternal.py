# -*- coding: utf-8 -*-
import time
import requests
import json

from odoo.http import request
from odoo.exceptions import ValidationError

from datetime import datetime, timedelta
from ..helpers import GoogleMaps


def get_access_token_internal(internal_id):
    try:
        if internal_id.expires_in > datetime.now():
            return internal_id
        # url =  'http://103.63.111.100:8088/api/auth/get_token'
        path = '/api/auth/get_token'
        url = internal_id.url + path
        account = internal_id.client_id
        password = internal_id.secret_key
        data = {
            'account': account,
            'password': password,
        }

        response = requests.post(url, data=json.dumps(data),
                                 headers={'Content-Type': 'application/json',
                                          'Cache-Control': 'no-cache',
                                          })
        response = response.json()
        if response.get('access_token'):
            expires_in = datetime.now() + timedelta(seconds=(float(response.get('expires_in'))) * 0.001)
            internal_id.access_token = response.get('access_token')
            internal_id.token_type = response.get('type')
            internal_id.expires_in = expires_in
            return internal_id
        else:
            return False
    except Exception as e:
        raise ValidationError(e)


def create_delivery_request(delivery_id):
    retry_times = 2
    while (retry_times > 0):
        try:
            access_token = get_access_token_internal(delivery_id.delivery_partner_id)
            if access_token:
                # url = 'http://103.63.111.100:8088/api/integrate/orders'
                path = '/api/integrate/orders'
                url = delivery_id.delivery_partner_id.url + path
                # distance = GoogleMaps.get_distance(delivery_id.address_sender, delivery_id.address_recipient)
                if delivery_id.type_origin == 'order':
                    type_ship = 'RETAIL'
                else:
                    type_ship = 'INTERNAL'
                orders = [
                    {
                        'orderNo': delivery_id.name,
                        'storeId': delivery_id.store_id.id,
                        'creator': delivery_id.sender_id.name,
                        'createAt': delivery_id.create_date.strftime("%d/%m/%Y %H:%M:%S"),
                        'totalPrice': delivery_id.total_price,
                        'shippingFee': 0,
                        'note': delivery_id.description,
                        'recvName': delivery_id.recipient_id,
                        'recvMobile': delivery_id.phone_recipient,
                        'recvAddress': delivery_id.address_recipient,
                        'recvFullAddress': delivery_id.address_recipient,
                        'recvEmail': '',
                        'recvLatitude': delivery_id.lat_recipient,
                        'recvLongitude': delivery_id.long_recipient,
                        "distance": delivery_id.distance,
                        "type": type_ship,
                    }, ]
                data = {
                    'orders': orders,
                }

                authorization = access_token.token_type + ' ' + access_token.access_token
                response = requests.post(url, data=json.dumps(data),
                                         headers={'Content-Type': 'application/json',
                                                  'authorization': authorization,
                                                  'Cache-Control': 'no-cache',
                                                  }, verify=False)
                retry_times -= 2
                delivery = response.json()
                return delivery
        except requests.exceptions.ConnectionError as e:
            retry_times -= 1
            # if we run out of times retry then raise error instead
            if retry_times == 0:
                raise ValidationError(e)
            time.sleep(1)
            continue
        except Exception as e:
            raise ValidationError(e)


def cancel_delivery(delivery_id):
    try:
        access_token = get_access_token_internal(delivery_id.delivery_partner_id)
        if access_token:
            # url = 'http://103.63.111.100:8088/api/integrate/order/cancel_order'
            path = '/api/integrate/order/cancel_order'
            url = delivery_id.delivery_partner_id.url + path
            data = {
                'orderNo': delivery_id.name,
                'note': 'Vận đơn dừng thực hiện',
            }
            authorization = access_token.token_type + ' ' + access_token.access_token
            response = requests.post(url, data=json.dumps(data),
                                     headers={'Content-Type': 'application/json',
                                              'authorization': authorization,
                                              'Cache-Control': 'no-cache',
                                              })
            response = response.json()
            if response.get('success') == True:
                return True
            else:
                return False
    except Exception as e:
        raise ValidationError(e)


def get_delivery_detail(delivery_id):
    retry_times = 2
    while (retry_times > 0):
        try:
            access_token = get_access_token_internal(delivery_id.delivery_partner_id)
            if access_token:
                # url = 'http://103.63.111.100:8088/api/integrate/order/get_detail'
                path = '/api/integrate/order/get_detail'
                url = delivery_id.delivery_partner_id.url + path
                data = {
                    'orderNo': delivery_id.name,
                }
                authorization = access_token.token_type + ' ' + access_token.access_token
                response = requests.post(url, data=json.dumps(data),
                                         headers={'Content-Type': 'application/json',
                                                  'authorization': authorization,
                                                  'Cache-Control': 'no-cache',
                                                  })
                delivery_detail = response.json()
                if 'id' in delivery_detail:
                    delivery_id.delivery_fee = delivery_detail.get('empBonus')
                    delivery_id.delivery_reference = delivery_detail.get('orderNo')
                    delivery_id.driver_name = delivery_detail.get('performerName')
                    delivery_id.license_plate = delivery_detail.get('performerCode')
                    delivery_id.state_delivery = delivery_detail.get('status')
                    if delivery_detail.get('status') == 'WAITING':
                        if delivery_id.state != 'waiting':
                            delivery_id.state = 'waiting'
                    if delivery_detail.get('status') == 'PROCESSING':
                        if delivery_id.state != 'delivering':
                            delivery_id.state = 'delivering'
                    if delivery_detail.get('status') in ('DELIVERY_SUCCESS', 'CLOSED'):
                        if delivery_id.state != 'done':
                            delivery_id.state = 'done'
                    if delivery_detail.get('status') == 'CANCELLED':
                        if delivery_id.state != 'cancel':
                            delivery_id.state = 'cancel'
                    if delivery_detail.get('status') == 'DELIVERY_FAIL':
                        if delivery_id.state != 'cancel':
                            delivery_id.state = 'cancel'
                else:
                    delivery_id.failed_reason = delivery_detail.get('message')
            retry_times -= 2
        except requests.exceptions.ConnectionError as e:
            retry_times -= 1
            # if we run out of times retry then raise error instead
            if retry_times == 0:
                raise ValidationError(e)
            time.sleep(1)
            continue
        except Exception as e:
            raise ValidationError(e)


def get_delivery_status(delivery_id):
    try:
        access_token = get_access_token_internal(delivery_id.delivery_partner_id)
        if access_token:
            # url = 'http://103.63.111.100:8088/api/integrate/order/get_status'
            path = '/api/integrate/order/get_status'
            url = delivery_id.delivery_partner_id.url + path
            data = {
                'orderNo': delivery_id.name,
            }
            authorization = access_token.token_type + ' ' + access_token.access_token
            response = requests.post(url, data=json.dumps(data),
                                     headers={'Content-Type': 'application/json',
                                              'authorization': authorization,
                                              'Cache-Control': 'no-cache',
                                              })
            delivery_detail = response.json()
            if 'orderNo' in delivery_detail:
                return delivery_detail.get('status')

    except Exception as e:
        raise ValidationError(e)
