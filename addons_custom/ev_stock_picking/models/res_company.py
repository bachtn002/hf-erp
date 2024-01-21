# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    x_allow_backorder = fields.Boolean('Allow Backorder')
