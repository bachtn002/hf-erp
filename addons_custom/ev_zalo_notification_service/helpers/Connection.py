# -*- coding: utf-8 -*-

from odoo.http import request


def check_allow_ip(ip):
    whitelist_ip = request.env['ip.send.zns'].sudo().search([('active', '=', True), ('name', '=', ip)])
    if whitelist_ip:
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
