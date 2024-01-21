import string
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta


class ProductPrompotionConfigLine(models.Model):
    _name = 'product.promotion.config.line'
    _description = 'Print Stamp Line'

    product_id = fields.Many2one(comodel_name='product.product', string="Product ID")
    price_unit_before = fields.Float(string="Price Before", default=0)
    price_unit = fields.Float(string="Price Unit", default=0)
    uom_id = fields.Many2one(comodel_name='uom.uom', string="Uom ID")
    packed_date = fields.Date(string="Packed Date")
    expire_date = fields.Date(string="Expire Date")
    note = fields.Text('Note')
    allow_printing = fields.Boolean('Allow Printing', default=False)
    name_above = fields.Char(string="Name above", size = 34)
    name_below = fields.Char(string="Name below", size = 34)

    promotion_config_id = fields.Many2one(comodel_name='product.promotion.config', string="Promotion Config ID")

    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     try:
    #         if self.promotion_config_id.stamp_type == 'promotion':
    #             line_ids = self.env['pos.promotion.qty.price'].search(
    #                 [('promotion_id', '=', self.promotion_config_id.promotion_id.id)])
    #             ids = []
    #             for line in line_ids:
    #                 ids.append(line.product_id.id)
    #             if self.product_id:
    #                 self.uom_id = self.product_id.product_tmpl_id.uom_id.id
    #                 # pricelist_item = self.env['product.pricelist.item'].sudo().search(
    #                 #     [('pricelist_id', '=', self.print_stamp_id.pricelist_id.id),
    #                 #         ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)])
    #                 # if pricelist_item:
    #                 #     price_unit = pricelist_item.fixed_price
    #                 # else:
    #                 price_unit = self.product_id.product_tmpl_id.list_price
    #                 self.price_unit = price_unit
    #                 self.packed_date = self.promotion_config_id.promotion_id.start_date
    #                 self.expire_date = self.promotion_config_id.promotion_id.end_date
    #                 for line in line_ids:
    #                     if line.product_id == self.product_id:
    #                         price = price_unit
    #                         if line.check_discount_price == 'price':
    #                             price = price_unit - line.price_unit
    #                         elif line.check_discount_price == 'discount':
    #                             price = price_unit - price_unit * (line.discount / 100)
    #                         self.price_unit = price
    #                         self.note = line.note
    #             else:
    #                 self.uom_id = None
    #                 self.price_unit = 0
    #                 self.note = None
    #                 self.packed_date = None
    #                 self.expire_date = None

    #         elif self.promotion_config_id.stamp_type == 'other':
    #             line_ids = self.env['product.product'].search(
    #                 [('product_tmpl_id', '=', self.id)])
    #             ids = []
    #             for line in line_ids:
    #                 ids.append(line.product_id.id)
    #             if self.product_id:
    #                 self.uom_id = self.product_id.product_tmpl_id.uom_id.id
    #                 price_unit = self.product_id.product_tmpl_id.list_price
    #                 self.price_unit = price_unit
    #                 self.packed_date = self.promotion_config_id.promotion_id.start_date
    #                 self.expire_date = self.promotion_config_id.promotion_id.end_date
    #     except Exception as e:
    #         raise ValidationError(e)
