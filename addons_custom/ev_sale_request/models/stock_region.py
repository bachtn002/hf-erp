# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class StockRegion(models.Model):
    _inherit = 'stock.region'

    x_supply_adjustment_ids = fields.Many2many('supply.adjustment', 'supply_adjustment_region', 'region_id',
                                               'supply_adjustment_id', string='Supply Adjustment')
