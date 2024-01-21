# -*- coding: utf-8 -*-
from odoo import models, fields, api


class LoyaltyProgram(models.Model):
    _inherit = 'loyalty.program'

    x_month_expire = fields.Integer('Month Expire')

