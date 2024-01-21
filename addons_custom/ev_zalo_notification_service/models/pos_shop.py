# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PosShop(models.Model):
    _inherit = 'pos.shop'

    x_oa_id = fields.Char('OA ID')
    x_app_id = fields.Char('APP ID')
    x_template_id = fields.Char('Template Send ZNS')

