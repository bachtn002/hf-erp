# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_round, float_compare


class ProductBarcode(models.Model):
    _name = 'product.barcode'
    _description = 'Product Barcode'

    _sql_constraints = [
        ('_unique_name', 'unique (name)', _("Name barcode must be unique")),
        ('positive_qty', 'CHECK(qty >= 0)', _('The quantity must be positive!'))
    ]

    @api.constrains('name')
    def _check_barcode_unique(self):
        barcodes = self.env['product.template'].search([]).mapped('barcode')
        for record in self:
            name = record.name.strip()
            if name in barcodes:
                raise ValidationError(_("Barcode should be unique in system!"))

    name = fields.Char("Barcode", required=1)
    qty = fields.Float("Quantity", required=1, default=1.0, digits='Product Unit of Measure', help="Number should be added to order when barcode scanned")
    product_tmpl_id = fields.Many2one('product.template', "Product")
    product_id = fields.Many2one('product.product', "Product")
    notes = fields.Text("Notes")
    active = fields.Boolean(related='product_tmpl_id.active', string="Active")

    @api.model
    def create(self, vals):
        res = super(ProductBarcode, self).create(vals)
        if res.product_tmpl_id and not res.product_id:
            product_id = self.env['product.product'].sudo().search([('product_tmpl_id', '=', res.product_tmpl_id.id)],
                                                                   limit=1)
            res.product_id = product_id.id
        elif res.product_id and not res.product_tmpl_id:
            res.product_tmpl_id = res.product_id.product_tmpl_id.id
        if not res.product_id and not res.product_tmpl_id:
            raise UserError(_("Barcode have to assign a product"))
        # rounding product qty
        rounding = res.product_tmpl_id.uom_id.rounding if res.product_tmpl_id else res.product_id.uom_id.rounding
        uom_qty = float_round(res.qty, precision_rounding=rounding, rounding_method='HALF-UP')
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        qty = float_round(res.qty, precision_digits=precision_digits, rounding_method='HALF-UP')
        if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
            raise UserError(
                _('The quantity for the product %s doesn\'t respect the rounding precision defined on the unit of measure %s. Please change the quantity done or the rounding precision of your unit of measure.') % (
                    res.product_id.display_name, res.product_id.uom_id.name))
        return res

    def write(self, values):
        res = super(ProductBarcode, self).write(values)
        rounding = self.product_tmpl_id.uom_id.rounding if self.product_tmpl_id else self.product_id.uom_id.rounding
        if res:
            # rounding product qty
            uom_qty = float_round(self.qty, precision_rounding=rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty = float_round(self.qty, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
                raise UserError(
                    _('The quantity for the product %s doesn\'t respect the rounding precision defined on the unit of measure %s. Please change the quantity done or the rounding precision of your unit of measure.') % (
                        self.product_id.display_name, self.product_id.uom_id.name))
        return res
