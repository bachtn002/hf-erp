# -*- coding: utf-8 -*-


from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_update_data = fields.Boolean('Update Data')