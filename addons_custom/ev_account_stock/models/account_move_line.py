# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    x_location_id = fields.Many2one('stock.location', 'Location')
    x_type_transfer = fields.Selection([('out','Out'),('in','In')], string='Type Transfer', default='out')
