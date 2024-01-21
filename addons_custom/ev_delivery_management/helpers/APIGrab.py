# -*- coding: utf-8 -*-

import requests
import json
import logging

from odoo import _
from odoo.http import request
from odoo.exceptions import ValidationError

from datetime import datetime, timedelta


def get_access_token_grab(partner_id):
    try:
        if partner_id.expires_in > datetime.now():
            return partner_id
        path = '/grabid/v1/oauth2/token'
        url_grab = partner_id.url
        url = url_grab.split('/')[0] + '//' + url_grab.split('/')[1] + url_grab.split('/')[2] + path
        client_id = partner_id.client_id
        client_secret = partner_id.secret_key
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
            'scope': 'grab_express.partner_deliveries',
        }
        response = requests.post(url, data=json.dumps(data),
                                 headers={'Content-Type': 'application/json',
                                          'Cache-Control': 'no-cache',
                                          })
        response = response.json()
        if response.get('access_token'):
            expires_in = datetime.now() + timedelta(seconds=float(response.get('expires_in')))
            partner_id.access_token = response.get('access_token')
            partner_id.token_type = response.get('token_type')
            partner_id.expires_in = expires_in
            return partner_id
        else:
            return False

    except Exception as e:
        raise ValidationError(e)


def get_delivery_quotes(delivery_id, grab_id):
    try:
        access_token = get_access_token_grab(grab_id)
        if not access_token:
            return False
        path = '/v1/deliveries/quotes'
        url = grab_id.url + path
        packages = [
            {
                'name': 'Đơn hàng ' + delivery_id.origin,
                'description': delivery_id.description if delivery_id.description else 'Đơn hàng ' + delivery_id.origin,
                'quantity': delivery_id.qty,
                'dimensions': {
                    'height': delivery_id.height,
                    'width': delivery_id.width,
                    'depth': delivery_id.depth,
                    'weight': int(delivery_id.weight * 1000)
                }
            }, ]
        origin = {
            'address': delivery_id.address_sender,
            'coordinates': {
                'latitude': float(delivery_id.lat_sender),
                'longitude': float(delivery_id.long_sender)
            }
        }
        destination = {
            'address': delivery_id.address_recipient,
            'coordinates': {
                'latitude': float(delivery_id.lat_recipient),
                'longitude': float(delivery_id.long_recipient)
            }
        }
        data = {
            'serviceType': 'INSTANT',
            'packages': packages,
            'origin': origin,
            'destination': destination,
        }
        authorization = access_token.token_type + ' ' + access_token.access_token
        response = requests.post(url, data=json.dumps(data),
                                 headers={'Content-Type': 'application/json',
                                          'authorization': authorization,
                                          'Cache-Control': 'no-cache',
                                          })
        quotes = response.json()
        if 'quotes' in quotes:
            return quotes['quotes'][0]['amount']
        else:
            return False
    except Exception as e:
        raise ValidationError(e)


def create_delivery_request(delivery_id):
    try:
        access_token = get_access_token_grab(delivery_id.delivery_partner_id)
        if not access_token:
            delivery_id.state = 'failed'
            delivery_id.failed_reason = _('Can not get Access Token')
            return
        url_grab = delivery_id.delivery_partner_id.url
        path = '/v1/deliveries'
        url = url_grab + path
        packages = [
            {
                'name': 'Đơn hàng ' + delivery_id.origin,
                'description': delivery_id.description if delivery_id.description else 'Đơn hàng ' + delivery_id.origin,
                'quantity': delivery_id.qty,
                'dimensions': {
                    'height': delivery_id.height,
                    'width': delivery_id.width,
                    'depth': delivery_id.depth,
                    'weight': int(delivery_id.weight * 1000)
                }
            }, ]
        origin = {
            'address': delivery_id.address_sender,
            'coordinates': {
                'latitude': float(delivery_id.lat_sender),
                'longitude': float(delivery_id.long_sender)
            }
        }
        destination = {
            'address': delivery_id.address_recipient,
            'coordinates': {
                'latitude': float(delivery_id.lat_recipient),
                'longitude': float(delivery_id.long_recipient)
            }
        }
        recipient = {
            'firstName': delivery_id.recipient_id,
            'phone': '84' + delivery_id.phone_recipient.lstrip('0'),
            'smsEnabled': True
        }
        sender = {
            'firstName': delivery_id.sender_id.name,
            'phone': '84' + delivery_id.phone_sender.lstrip('0'),
            'smsEnabled': True
        }
        cash_on_delivery = {
            'amount': int(delivery_id.cod)
        }
        data = {
            'merchantOrderID': delivery_id.name,
            'serviceType': 'INSTANT',
            'packages': packages,
            'origin': origin,
            'destination': destination,
            'recipient': recipient,
            'sender': sender,
            'cashOnDelivery': cash_on_delivery,
        }

        authorization = access_token.token_type + ' ' + access_token.access_token
        response = requests.post(url, data=json.dumps(data),
                                 headers={'Content-Type': 'application/json',
                                          'authorization': authorization,
                                          'Cache-Control': 'no-cache',
                                          })
        delivery = response.json()
        return delivery
    except Exception as e:
        raise ValidationError(e)


def cancel_delivery(delivery_id):
    try:
        access_token = get_access_token_grab(delivery_id.delivery_partner_id)
        if access_token:
            url_grab = delivery_id.delivery_partner_id.url
            path = '/v1/deliveries/'
            url = url_grab + path + delivery_id.delivery_reference
            authorization = access_token.token_type + ' ' + access_token.access_token
            response = requests.delete(url, headers={'Content-Type': 'application/json',
                                                     'authorization': authorization,
                                                     'Cache-Control': 'no-cache',
                                                     })
            try:
                return response.json()
            except:
                return True
    except Exception as e:
        raise ValidationError(e)


def get_delivery_detail(delivery_id):
    try:
        access_token = get_access_token_grab(delivery_id.delivery_partner_id)
        if access_token:
            url_grab = delivery_id.delivery_partner_id.url
            path = '/v1/deliveries/'
            url = url_grab + path + delivery_id.delivery_reference
            authorization = access_token.token_type + ' ' + access_token.access_token
            response = requests.get(url, headers={'Content-Type': 'application/json',
                                                  'authorization': authorization,
                                                  'Cache-Control': 'no-cache',
                                                  })
            if response.status_code == 200:
                response = response.json()
                delivery_id.state_delivery = response.get('status')
                if response.get('status') == 'ALLOCATING' and delivery_id.state != 'waiting':
                    delivery_id.driver_name = None
                    delivery_id.driver_phone = None
                    delivery_id.license_plate = None
                    delivery_id.state = 'waiting'
                if response.get('status') == 'PICKING_UP' and delivery_id.state != 'pickup':
                    delivery_id.state = 'pickup'
                if response.get('status') == 'IN_DELIVERY' and delivery_id.state != 'delivering':
                    delivery_id.state = 'delivering'
                if response.get('status') in ('COMPLETED', 'RETURNED') and delivery_id.state != 'done':
                    delivery_id.state = 'done'
                if response.get('status') == 'FAILED' and delivery_id.state != 'failed':
                    delivery_id.state = 'failed'
                if response.get('status') == 'CANCELED' and delivery_id.state != 'cancel':
                    delivery_id.state = 'cancel'
                if response.get('courier'):
                    delivery_id.driver_name = response.get('courier').get('name')
                    delivery_id.driver_phone = response.get('courier').get('phone')
                    delivery_id.license_plate = response.get('courier').get('vehicle').get(
                        'licensePlate') if response.get('courier').get('vehicle') else None

                delivery_id.track_url = response.get('trackingURL')
                delivery_id.pickup_pin = response.get('pickupPin')
                delivery_id.failed_reason = response.get('advanceInfo').get('failedReason') if response.get(
                    'advanceInfo') else None
            elif response.status_code == 401:
                response = response.json()
                delivery_id.failed_reason = str(response)
    except Exception as e:
        raise ValidationError(e)
