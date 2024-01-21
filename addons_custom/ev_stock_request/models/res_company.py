# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    x_auto_create_transfer = fields.Boolean('Auto create transfer')
