# -*- coding: utf-8 -*-
# Created by Hoanglv on 8/14/2019

from .Response import Response


class ApiException(Exception):

    ERROR = 400
    AUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    PARAM_NOT_PROVIDE = 406
    INVALID_ACCESS_TOKEN = 407
    INVALID_DATA_TYPE = 408
    INVALID_DATA_FORMAT = 409
    VALUE_NOT_NULL = 410
    UNKNOWN_ERROR = 411
    METHOD_NOT_FOUND = 412
    ACCESS_DENIED = 413

    def __init__(self, message, code=0):
        self.message = message
        self.code = code

    def to_json(self):
        return Response.error(self.message, code=self.code).to_json()
