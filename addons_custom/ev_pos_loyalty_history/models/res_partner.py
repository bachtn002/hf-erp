# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_customer_point_history_ids = fields.One2many('customer.point.history', 'partner_id', 'Customer Point History')

