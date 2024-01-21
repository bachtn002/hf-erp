# -*- coding: utf-8 -*-

from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    x_allow_return_before_day = fields.Integer(string='Allow return before day')
