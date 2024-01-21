from odoo import api, fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    warehouse_voucher = fields.Boolean('Warehouse voucher')
