# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    sinvoice_tax_amount = fields.Float(string='Sinvoice Tax Amount')