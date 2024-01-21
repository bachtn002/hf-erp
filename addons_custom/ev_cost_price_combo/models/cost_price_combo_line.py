from odoo import fields, models, api, _

from odoo.exceptions import UserError, ValidationError


class CostPriceComboLine(models.Model):
    _name = 'cost.price.combo.line'
    _order = 'create_date desc'

    product_id = fields.Many2one('product.product', string='Product',
                                 domain=[('x_is_combo', '=', True), ('active', '=', True)])
    uom_id = fields.Many2one('uom.uom', string='Uom', readonly=True)
    cost_price = fields.Float(string='Cost Price', default=0)

    detail_ids = fields.One2many('cost.price.combo.detail', 'cost_price_combo_line_id',
                                 string='Cost Price Combo Detail')
    cost_price_combo_id = fields.Many2one('cost.price.combo', string='Cost Price Combo')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        try:
            self.uom_id = self.product_id.product_tmpl_id.uom_id
        except Exception as e:
            raise ValidationError(e)
