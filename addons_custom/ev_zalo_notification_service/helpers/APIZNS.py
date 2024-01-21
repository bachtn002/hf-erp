# -*- coding: utf-8 -*-
from time import sleep
import requests
import json
import logging

from datetime import datetime, timedelta, date

from odoo.http import request
from odoo.exceptions import ValidationError, UserError
from odoo import _

from ..helpers import APIGetToken

_logger = logging.getLogger(__name__)


def get_template(zns_id, offset, limit, status=False):
    try:
        access_token = APIGetToken.get_access_token(zns_id.oa_id, zns_id.app_id)
        if not access_token:
            raise UserError(_('Do not access token'))
        url = 'https://business.openapi.zalo.me/template/all'
        data = {
            'offset': offset,
            'limit': limit,
        }
        if status:
            data = {
                'offset': offset,
                'limit': limit,
                'status': status,
            }
        response = requests.get(url, params=data,
                                headers={'Content-Type': 'application/json',
                                         'access_token': access_token,
                                         })
        template = response.json()
        list_id = []
        for dt in template.get('data'):
            # created_time = datetime.fromtimestamp(float(dt['createdTime']) / 1000)
            template = request.env['zns.template'].sudo().search([('template_id', '=', dt.get('templateId'))])
            if not template:
                vals = {
                    'template_id': dt.get('templateId'),
                    'template_name': dt.get('templateName'),
                    'oa_id': zns_id.oa_id,
                    'app_id': zns_id.app_id,
                    'created_time': dt.get('createdTime'),
                    'status': str(dt.get('status')).lower(),
                    'template_quality': str(dt.get('templateQuality')).lower(),
                }
                template_id = request.env['zns.template'].sudo().create(vals)
                list_id.append(template_id.id)
        list_template = request.env['zns.template'].sudo().search([('id', 'in', list_id)])
        return list_template
    except Exception as e:
        raise ValidationError(e)


def get_template_detail(template_id):
    try:
        access_token = APIGetToken.get_access_token(template_id.oa_id, template_id.app_id)
        if not access_token:
            raise UserError(_('Do not access token'))
        url = 'https://business.openapi.zalo.me/template/info'

        data = {
            'template_id': template_id.template_id,
        }

        response = requests.get(url, params=data,
                                headers={'Content-Type': 'application/json',
                                         'access_token': access_token,
                                         })
        detail = response.json()
        # timeout = datetime.fromtimestamp(detail['data']['timeout'])

        template_daily_quota = False
        template_remaining_quota = False
        list_params = []
        if detail.get('error') != 0:
            return
        for param in detail.get('data').get('listParams'):
            list = {
                'name': param.get('name'),
                'require': param.get('require'),
                'type': param.get('type'),
                'max_length': param.get('maxLength'),
                'min_length': param.get('minLength'),
                'accept_null': param.get('acceptNull'),
            }
            list_params.append([0, 0, list])

        if detail.get('data').get('applyTemplateQuota'):
            template_daily_quota = detail('data').get('templateDailyQuota')
            template_remaining_quota = detail('data').get('templateRemainingQuota')
        vals = {
            'timeout': detail.get('data').get('timeout'),
            'preview_url': detail.get('data').get('previewUrl'),
            'template_tag': str(detail.get('data').get('templateTag')).lower(),
            'price': float(detail.get('data').get('price')),
            'apply_template_quota': detail.get('data').get('applyTemplateQuota'),
            'template_daily_quota': template_daily_quota,
            'template_remaining_quota': template_remaining_quota,
            'list_params': list_params,
        }
        template_detail = template_id.update(vals)
        return template_detail
    except Exception as e:
        raise ValidationError(e)


# def send_zns(order_id, zns_infor):
#     try:
#         url = 'https://business.openapi.zalo.me/message/template'
#
#         access_token = APIGetToken.get_access_token()
#         if not access_token:
#             raise UserError(_('Do not access token'))
#
#         template_id = request.env['zns.template'].sudo().search([('template_id', '=', '219951')], limit=1)
#         order_date = datetime.strftime(order_id.date_order + timedelta(hours=7), '%H:%m %d/%m/%Y')
#
#         phone = '84' + order_id.partner_id.phone.lstrip('0')
#
#         data = {
#             'phone': phone,
#             'template_id': template_id.template_id,
#             'template_data': {
#                 'customer_name': order_id.partner_id.name,
#                 'order_code': order_id.pos_reference,
#                 'order_date': order_date,
#                 'order_value': int(order_id.amount_total),
#                 'point_plus': int(order_id.loyalty_points),
#                 'point_value': int(order_id.partner_id.loyalty_points),
#             },
#             'tracking_id': zns_infor.tracking_id,
#         }
#
#         response = requests.post(url, data=json.dumps(data),
#                                  headers={'Content-Type': 'application/json',
#                                           'access_token': access_token,
#                                           })
#         response = response.json()
#
#         if str(response['error']) == '0':
#             sent_time = datetime.fromtimestamp(float(response['data']['sent_time']) / 1000).strftime(
#                 '%Y-%m-%d %H:%M:%S')
#             date_convert = datetime.strptime(sent_time, '%Y-%m-%d %H:%M:%S')
#
#             zns_infor.msg_id = response['data']['msg_id']
#             zns_infor.sent_time = date_convert
#             zns_infor.state = 'done'
#             zns_infor.mess_error = None
#             zns_infor.data = data
#
#             return zns_infor
#         else:
#             zns_infor.state = 'error'
#             zns_infor.mess_error = response['message']
#             zns_infor.data = data
#             return zns_infor
#     except Exception as e:
#         raise ValidationError(e)


def send_zns_otp(app_id, oa_id, otp, phone):
    try:
        url = 'https://business.openapi.zalo.me/message/template'
        access_token = APIGetToken.get_access_token(oa_id, app_id)
        if not access_token:
            raise UserError(_('Do not access token'))

        zalo_oa = request.env['zalo.official.account'].sudo().search(
            [('oa_id', '=', oa_id), ('app_id', '=', app_id), ('active', '=', True)], limit=1)
        if not zalo_oa:
            return False
        phone = '84' + phone.lstrip('0')

        data = {
            'phone': phone,
            'template_id': zalo_oa.template_otp,
            'template_data': {
                'otp': otp,
            },
            'tracking_id': otp + phone,
        }

        response = requests.post(url, data=json.dumps(data),
                                 headers={'Content-Type': 'application/json',
                                          'access_token': access_token,
                                          })
        response = response.json()
        if str(response.get('error')) == '0':
            return True
        else:
            if str(response.get('error')) == '-211':
                return _('ZNS message limit expired')
            return False
    except Exception as e:
        raise ValidationError(e)


def get_profile(user_id, app_id, oa_id):
    retry_times = 2
    while (retry_times > 0):
        try:
            url = 'https://openapi.zalo.me/v2.0/oa/getprofile?data={"user_id":\"%s\"}' % user_id

            access_token = APIGetToken.get_access_token(oa_id, app_id)
            if not access_token:
                raise UserError(_('Do not access token'))

            response = requests.get(url,
                                    headers={'Content-Type': 'application/json',
                                             'access_token': access_token,
                                             }, verify=False)
            response = response.json()
            retry_times -= 2
            if str(response.get('error')) == '-213':
                return False
            else:
                return True
        except requests.exceptions.ConnectionError as e:
            retry_times -= 1
            # if we run out of times retry then raise error instead
            if retry_times == 0:
                raise ValidationError(e)
            sleep(1)
            continue
        except Exception as e:
            raise ValidationError(e)
