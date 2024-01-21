from odoo import models, fields, api


class product(models.Model):
    _inherit = 'product.template'

    x_supply_type = fields.Selection([
        ('warehouse', 'Warehouse'),
        ('purchase', 'Purchase'),
        ('stop_supply', 'Stop Supply')],
        string='Product supply category', default=False, track_visibility='always', required=False)

    # x_supply_adjustment_ids = fields.Many2many('supply.adjustment', 'supply_adjustment_product', 'product_id',
    #                                            'supply_adjustment_id', string='Supply Adjustment')
