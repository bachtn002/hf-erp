from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, float_compare


class StockTransferLine(models.Model):
    _inherit = 'stock.transfer.line'

    # quantity packed
    qty_packed = fields.Float('Quantity Packed', digits='Product Unit of Measure', readonly=True)
    # SL sản phẩm rời được scan, technical field sử dụng để thay thế vòng lặp tất cả thùng đc scan
    # để lấy số lượng của cùng sp đc đóng thùng
    product_qty_scanned = fields.Float('Quantity Packed', default=0, digits='Product Unit of Measure')

    @api.constrains('product_qty_scanned')
    def _check_qty_done(self):
        try:
            for rec in self:
                uom_qty = float_round(rec.product_qty_scanned, precision_rounding=rec.product_uom.rounding, rounding_method='HALF-UP')
                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                qty = float_round(rec.product_qty_scanned, precision_digits=precision_digits, rounding_method='HALF-UP')
                if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
                    raise UserError(
                        _('The quantity for the product %s doesn\'t respect the rounding precision defined on the unit of measure %s. Please change the quantity done or the rounding precision of your unit of measure.') % (
                            rec.product_id.display_name, rec.product_uom.name))
        except Exception as e:
            raise ValidationError(e)

    @api.onchange('product_qty_scanned')
    def onchange_quantity(self):
        if self.product_qty_scanned:
            # rounding product qty
            rounding = self.product_uom.rounding if self.product_uom else self.product_id.uom_id.rounding
            uom_qty = float_round(self.product_qty_scanned, precision_rounding=rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty = float_round(self.product_qty_scanned, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
                raise UserError(
                    _('The quantity for the product %s doesn\'t respect the rounding precision defined on the unit of measure %s. Please change the quantity done or the rounding precision of your unit of measure.') % (
                        self.product_id.name, self.product_uom.name))

    def update_transfer_line_quantity(self, line_id, **kwargs):
        in_quantity = out_quantity = 0
        line_to_update = self.env['stock.transfer.line'].browse(line_id)
        """Update quantity form scan package
        +) product_qty_scanned is the quantity of product outside the packages and 
            will be update from write method and pass it's value to this method 
            so we don't have worry about the time scan quantity and out/in quantity update time are different
        +) we will update in/out quantity based on formular qty_update = last_qty (is origin_qty) + in/out + product_qty_scanned
        """
        if kwargs.get('in_quantity'):
            in_quantity += kwargs['in_quantity']
        if kwargs.get('out_quantity'):
            out_quantity += kwargs['out_quantity']
        if line_to_update:
            if line_to_update.stock_transfer_id.state != 'transfer':
                line_to_update.out_quantity = line_to_update.out_quantity + out_quantity
            else:
                line_to_update.in_quantity = line_to_update.in_quantity + in_quantity