from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_round, float_compare


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.constrains('barcode')
    def _check_barcode_unique(self):
        multi_barcodes = self.env['product.barcode'].search([]).mapped('name')
        barcodes = self.env['product.template'].mapped('barcode')
        for record in self:
            if record.barcode:
                barcode = record.barcode.strip()
                if barcode in multi_barcodes or barcode in barcodes:
                    raise ValidationError(_("Barcode should be unique in system!"))

    x_barcode_ids = fields.One2many("product.barcode", "product_tmpl_id", string="Multi Barcodes")

    def write(self, values):
        res = super(ProductTemplate, self).write(values)
        if res:
            # rounding product qty
            rounding = self.uom_id.rounding
            for barcode in self.x_barcode_ids:
                uom_qty = float_round(barcode.qty, precision_rounding=rounding,
                                      rounding_method='HALF-UP')
                precision_digits = barcode.env['decimal.precision'].precision_get('Product Unit of Measure')
                qty = float_round(barcode.qty, precision_digits=precision_digits, rounding_method='HALF-UP')
                if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
                    raise UserError(
                        _('The quantity for the product %s doesn\'t respect the rounding precision defined on the unit of measure %s. Please change the quantity done or the rounding precision of your unit of measure.') % (
                            barcode.product_id.display_name, barcode.product_id.uom_id.name))
                # Update product relationship
                if barcode.product_tmpl_id and not barcode.product_id:
                    product_id = self.env['product.product'].sudo().search(
                        [('product_tmpl_id', '=', barcode.product_tmpl_id.id)], limit=1)
                    barcode.product_id = product_id.id
                elif barcode.product_id and not barcode.product_tmpl_id:
                    barcode.product_tmpl_id = barcode.product_id.product_tmpl_id.id
                if not barcode.product_id and not barcode.product_tmpl_id:
                    raise UserError(_("Barcode have to assign a product"))
        return res

    @api.model
    def create(self, values):
        res = super(ProductTemplate, self).create(values)
        # rounding product qty
        for barcode in res.x_barcode_ids:
            uom_qty = float_round(barcode.qty, precision_rounding=res.uom_id.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty = float_round(barcode.qty, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
                raise UserError(
                    _('The quantity for the product %s doesn\'t respect the rounding precision defined on the unit of measure %s. Please change the quantity done or the rounding precision of your unit of measure.') % (
                        res.name, res.uom_id.name))
        return res


class Product(models.Model):
    _inherit = 'product.product'

    @api.constrains('barcode')
    def _check_barcode_unique(self):
        multi_barcodes = self.env['product.barcode'].search([]).mapped('name')
        barcodes = self.env['product.product'].mapped('barcode')
        for record in self:
            if record.barcode:
                barcode = record.barcode.strip()
                if barcode in multi_barcodes or barcode in barcodes:
                    raise ValidationError(_("Barcode should be unique in system!"))

    x_barcode_ids = fields.One2many("product.barcode", "product_id", string="Multi Barcodes")
