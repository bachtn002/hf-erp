# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CustomerPointHistory(models.Model):
    _name = 'customer.point.history'
    _order = 'create_date ASC'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Customer point history'

    partner_id = fields.Many2one('res.partner', string="Partner")
    points = fields.Float(string="Point")
    expire_date = fields.Datetime('Expire date Point')
    type = fields.Selection([
        ('accumulate_point', 'Accumulate Point'),
        ('focus_point', 'Focus Point')], default=None, string="Type")

    order_id = fields.Many2one('pos.order', string='Order')
