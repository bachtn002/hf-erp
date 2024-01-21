from odoo import fields, models, api, _

from odoo.exceptions import UserError, ValidationError


class CostPriceComboDetail(models.Model):
    _name = 'cost.price.combo.detail'
    _order = 'create_date desc'

    product_id = fields.Many2one('product.product', string='Product',
                                 domain=[('x_is_combo', '=', True), ('active', '=', True)])
    quantity = fields.Float(string='Quantity')
    cost_price = fields.Float(string='Cost Price')

    cost_price_combo_line_id = fields.Many2one('cost.price.combo.line', string='Cost Price Combo Line')
