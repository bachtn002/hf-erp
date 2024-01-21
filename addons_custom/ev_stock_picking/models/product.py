from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def print_stamp(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_picking.stamp_printing_product_product_lot/%s' % self.id,
            'target': 'new',
        }
