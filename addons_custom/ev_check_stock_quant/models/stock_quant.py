# -*- coding: utf-8 -*-


from odoo import models, fields, api, _


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    x_update_data = fields.Boolean('Update Data')