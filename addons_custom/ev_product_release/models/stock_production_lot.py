from odoo import api, fields, models


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    x_release_id = fields.Many2one('product.release', 'Product release')
    x_order_id = fields.Many2one('pos.order', 'Order')
    x_order_use_id = fields.Many2one('pos.order', 'Order use')
    x_customer_id = fields.Many2one('res.partner', 'Customer')
    x_use_customer_id = fields.Many2one('res.partner', 'Use customer')
    x_total_count = fields.Float('Total count')
    x_use_count = fields.Float('Use count')
    x_state = fields.Selection(selection=[
        ('new', 'New'),
        ('activated', 'Activated'),
        ('available', 'Available'),
        ('used', 'Used'),
        ('expired', 'Expired'),
        ('destroy', 'Destroy'),
        ('lock', 'Lock')
    ], default='new', string='State', )
    name_product_release = fields.Char('Product release name', related='x_release_id.name', store=True)
