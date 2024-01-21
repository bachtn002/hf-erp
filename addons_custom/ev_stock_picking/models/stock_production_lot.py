from odoo import api, fields, models


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    def print_stamp_production_lot(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_picking.stock_production_lot_temp_printing/%s' % self.id,
            'target': 'new',
        }
