# -*- coding: utf-8 -*-
# Created by Hoanglv on 8/18/2019

import re

from .ApiException import ApiException
from odoo import _


class Email(object):

    @staticmethod
    def validate(email, error_message=''):
        pattern = r'[\w\.]+@[\w]{2,6}.([a-z]{2,6}){1,3}'
        if not re.search(pattern, email):
            raise ApiException(error_message or _('Email format is incorrect'), ApiException.INVALID_DATA_FORMAT)
        return True
