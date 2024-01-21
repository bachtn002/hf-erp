# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date


class SaleOnlineOrderLine(models.Model):
    _name = 'sale.online.order.line'

    product_id = fields.Many2one('product.template', string='product', domain=[('sale_ok', '=', True), ('available_in_pos','=',True)])
    price = fields.Float(string='price', compute='_compute_price', store=True)

    amount = fields.Float(string='amount total', default=0, compute='_compute_amount',store=True)

    uom = fields.Many2one('uom.uom', string='uom', domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)

    quantity = fields.Float(string='Quantity', digits='Product Unit of Measure')

    sale_online_id = fields.Many2one('sale.online', string='sale online id')

    @api.onchange('product_id', 'quantity')
    @api.depends('product_id', 'quantity')
    def _compute_amount(self):
        for record in self:
            record._compute_price()
            record.amount = record.price * record.quantity

    def _compute_price(self):
        for record in self:
            if not record.sale_online_id.is_created_by_api:
                record.price = 0
                pricelist_item = self.env['product.pricelist.item'].sudo().search(
                    [('pricelist_id', '=', record.sale_online_id.price_list_id.id),
                     ('product_tmpl_id', '=', record.product_id.id), '|', ('date_end', '=', False),
                     ('date_end', '>=', datetime.today()), '|', ('date_start', '=', False), ('date_start', '<=', datetime.today())], limit=1)
                if pricelist_item:
                    price_unit = pricelist_item.fixed_price
                else:
                    price_unit = record.product_id.list_price
                record.price = price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            record.uom = record.product_id.uom_id.id

    @api.constrains('quantity')
    def check_uom_line(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_("The number of product must be greater than 0!!"))
            else:
                uom_qty = float_round(line.quantity, precision_rounding=line.uom.rounding, rounding_method='HALF-UP')
                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                qty = float_round(line.quantity, precision_digits=precision_digits, rounding_method='HALF-UP')
                if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
                    raise UserError(
                        _('The quantity done for the product "%s" doesn\'t respect the rounding precision defined on the unit of measure "%s". Please change the quantity done or the rounding precision of your unit of measure.') % (
                        line.product_id.display_name, line.uom.name))
