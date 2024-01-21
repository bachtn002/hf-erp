# -*- coding: utf-8 -*-

import requests

from odoo import models, fields, _


class ZaloToken(models.Model):
    _inherit = 'zalo.token'

    oa_id = fields.Char('OA ID', required=True)

