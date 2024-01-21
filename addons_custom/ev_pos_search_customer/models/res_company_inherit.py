# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    x_number_search_limit = fields.Integer(string=_('Number Search Customer Limit'))
    x_apply_fix_customer = fields.Boolean(string=_('Apply fix customer'))
