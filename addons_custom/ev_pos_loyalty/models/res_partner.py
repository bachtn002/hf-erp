# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_rank_id = fields.Many2one('customer.rank',string="Customer Rank")
    x_date_rank = fields.Date('Date Rank')
    x_customer_rank_history_ids = fields.One2many('customer.rank.history', 'partner_id', 'Customer rank history')
    x_customer_point_history_ids = fields.One2many('customer.point.history', 'partner_id', 'Customer Point History')

