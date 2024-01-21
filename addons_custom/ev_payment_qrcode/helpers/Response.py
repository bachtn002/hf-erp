# -*- coding: utf-8 -*-

import json

from odoo import _, tools
from odoo.http import request, Response as OdooResponse


class Response(object):
    SUCCESS = 200
    ERROR = 400

    __CODE = ''
    __MESSAGE = ''
    __DATA = {}

    __DEFAULT_ERROR_MESSAGE = _('An error occurred, please try again later.')

    __instance = None

    @staticmethod
    def get_instance():
        if not Response.__instance:
            Response()
        return Response.__instance

    def __init__(self):
        if not Response.__instance:
            Response.__instance = self

    @staticmethod
    def success(message, data):
        Response.__CODE = Response.SUCCESS
        Response.__set_message_data(message, data)
        return Response

    @staticmethod
    def error(message=False, data={}, code=False):
        Response.__CODE = code or Response.ERROR
        Response.__set_message_data(message or Response.__DEFAULT_ERROR_MESSAGE, data)
        return Response

    @staticmethod
    def to_json():
        if request._request_type == 'http':
            return OdooResponse(json.dumps(Response.__generate_template_get_method()),
                                content_type='application/json;charset=utf-8',
                                status=200)
        return Response.__generate_template()

    @staticmethod
    def to_string():
        if request._request_type == 'http':
            return OdooResponse(json.dumps(Response.__generate_template_get_method()),
                                content_type='text/plain;charset=utf-8',
                                status=200)
        return OdooResponse(json.dumps(Response.__generate_template()),
                            content_type='text/plain;charset=utf-8',
                            status=200)

    @staticmethod
    def __set_message_data(message, data):
        Response.__MESSAGE = message
        Response.__DATA = data

    @staticmethod
    def __generate_template():
        return {
            "code": Response.__CODE,
            "message": Response.__MESSAGE,
            "data": Response.__DATA
        }

    @staticmethod
    def __generate_template_get_method():
        return {
            'result': Response.__generate_template()
        }

    @staticmethod
    def __get_db_name():
        if tools.config.options.get('db_name'):
            return tools.config.options.get('db_name')
        return tools.config.options.get('dbfilter')
