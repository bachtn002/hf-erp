# -*- coding: utf-8 -*-
# Created by Hoanglv on 8/7/2019

import re
from odoo import _

from .ApiException import ApiException


class PhoneNumber(object):

    __PHONE_NUMBER_CONVERT_PREFIX__ = {'0162': '032', '0163': '033', '0164': '034', '0165': '035', '0166': '036',
                                       '0167': '037', '0168': '038', '0169': '039', '0120': '070', '0121': '079',
                                       '0122': '077', '0126': '076', '0128': '078', '0123': '083', '0124': '084',
                                       '0125': '085', '0127': '081', '0129': '082', '0186': '056', '0188': '058',
                                       '0199': '059'}

    @staticmethod
    def validate(phone_number, error_message=''):
        if not phone_number or phone_number == '':
            return True
        phone_number = phone_number.strip()
        pattern = r'0{1}[0-9]{9,10}'
        if not re.fullmatch(pattern, phone_number):
            raise ApiException(error_message or _('Phone number must be start with "0" and it\'s length between 10 and 11')
                               , ApiException.INVALID_DATA_FORMAT)
        return True

    @staticmethod
    def convert(phone_number):
        phone_number = phone_number.strip()
        if phone_number.find('+84') == 0:
            phone_number.repleace('+84', '0')
        new_prefix = PhoneNumber.__PHONE_NUMBER_CONVERT_PREFIX__.get(phone_number[0:4])
        if len(phone_number) == 11 and new_prefix:
            phone_number.replace(phone_number[0:4], new_prefix, 1)
        return phone_number
