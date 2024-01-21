# -*- coding: utf-8 -*-

import pytz
from datetime import datetime, timedelta
from odoo.http import request


def check_allow_ip(ip):
    whitelist_ips = request.env['ip.connection'].sudo().search([('active', '=', True)])
    if ip in whitelist_ips.mapped('name'):
        return True
    else:
        return False


def get_request_ip():
    """
    :return: public ip address
    """
    ip = request.httprequest.headers.environ['REMOTE_ADDR']
    if 'HTTP_X_FORWARDED_FOR' in request.httprequest.headers.environ \
            and request.httprequest.headers.environ['HTTP_X_FORWARDED_FOR']:
        forwarded_for = request.httprequest.headers.environ['HTTP_X_FORWARDED_FOR'].split(', ')
        if forwarded_for and forwarded_for[0]:
            ip = forwarded_for[0]
    return ip


def _set_log_api(ip, api, name, params, code, mess):
    vals = {
        'remote_ip': ip,
        'code_api': api,
        'name_api': name,
        'params': params,
        'code_response': code,
        'mess_response': mess,
    }
    request.env['log.api'].sudo().create(vals)
    return


def _get_api_config(params):
    """ function check token matching with config api
    @return: Api config if everything is valid
             Return False otherwise
    """
    api_config = request.env['config.api'].sudo().search([('token', '=', params), ('active', '=', True)], limit=1)
    return api_config


def get_hour_tz_by_user(user):
    tz = pytz.timezone(user.partner_id.tz) if user.partner_id.tz else pytz.utc
    current_time = datetime.now(tz)
    hour_tz = int(str(current_time)[-5:][:2])
    min_tz = int(str(current_time)[-5:][3:])
    sign = str(current_time)[-6][:1]
    if sign == '+':
        hour_tz = -hour_tz
        min_tz = -min_tz
    return hour_tz, min_tz, sign


def convert_from_date_to_date_global(start, end, user):
    hour_tz, min_tz, sign = get_hour_tz_by_user(user)
    sdate = start + " 00:00:00"
    edate = end + " 23:59:59"
    start_date = (datetime.strptime(sdate, '%Y-%m-%d %H:%M:%S') + timedelta(hours=hour_tz,
                                                                            minutes=min_tz)).strftime(
        "%Y-%m-%d %H:%M:%S")
    end_date = (datetime.strptime(edate, '%Y-%m-%d %H:%M:%S') + timedelta(hours=hour_tz,
                                                                          minutes=min_tz)).strftime(
        "%Y-%m-%d %H:%M:%S")
    return start_date, end_date