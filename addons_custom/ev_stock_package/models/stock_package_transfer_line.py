from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_round, float_compare


class StockPackageTransferLine(models.Model):
    _name = 'stock.package.transfer.line'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string="Product ID")
    qty = fields.Float(string="Quantity", digits='Product Unit of Measure')
    qty_done = fields.Float(string="Quantity Done", digits='Product Unit of Measure')
    uom_id = fields.Many2one('uom.uom', string="Uom ID")
    package_transfer_id = fields.Many2one('stock.package.transfer', string="Package Transfer ID")

    product_barcode = fields.Char(related='product_id.barcode')

    @api.constrains('qty_done')
    def _check_qty_done(self):
        try:
            for rec in self:
                uom_qty = float_round(rec.qty_done, precision_rounding=rec.uom_id.rounding, rounding_method='HALF-UP')
                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                qty = float_round(rec.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
                if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
                    raise UserError(
                        _('The quantity for the product %s doesn\'t respect the rounding precision defined on the unit of measure %s. Please change the quantity done or the rounding precision of your unit of measure.') % (
                            rec.product_id.display_name, rec.product_id.uom_id.name))
        except Exception as e:
            raise ValidationError(e)
