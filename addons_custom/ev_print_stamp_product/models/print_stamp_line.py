from email.policy import default
import string
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date


class PrintStampLine(models.TransientModel):
    _name = 'print.stamp.line'
    _description = 'Print Stamp Line'

    product_id = fields.Many2one(comodel_name='product.product', string="Product ID")
    price_unit_before = fields.Float(string="Price Before", default=0)
    price_unit = fields.Float(string="Price Unit", default=0)
    uom_id = fields.Many2one(comodel_name='uom.uom', string="Uom ID")
    packed_date = fields.Date(string="Packed Date")
    expire_date = fields.Date(string="Expire Date")
    note = fields.Text('Note')
    allow_printing = fields.Boolean('Allow Printing', default=False)
    qty_printing = fields.Integer('Print Quantity', default = 0)
    name_above = fields.Char(string="Name above", size = 34)
    name_below = fields.Char(string="Name below", size = 34)
    origin = fields.Char(string="Origin")
    empty_date = fields.Boolean('Empty date', default=False )

    print_stamp_id = fields.Many2one(comodel_name='print.stamp', string="Print Stamp ID")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        try:
            if self.print_stamp_id.shop_id:
                if self.print_stamp_id.stamp_type in ('shelf', 'product'):
                    product_ids = self.env['product.product'].search(
                        [('product_tmpl_id', 'in', self.print_stamp_id.shop_id.product_ids.ids)])

                    domain = ['|', ('id', 'in', product_ids.ids), ('product_tmpl_id.x_print_stamp', '=', True)]
                    if self.product_id:
                        self.uom_id = self.product_id.product_tmpl_id.uom_id.id
                        pricelist_item = self.env['product.pricelist.item'].sudo().search(
                            [('pricelist_id', '=', self.print_stamp_id.pricelist_id.id),
                             ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id), '|',('date_end','=',False),('date_end','>=',datetime.today()),
                             '|', ('date_start', '=', False), ('date_start', '<=', datetime.today())], limit=1)
                        if pricelist_item:
                            self.price_unit = pricelist_item.fixed_price
                        else:
                            self.price_unit = self.product_id.product_tmpl_id.list_price
                    else:
                        self.uom_id = None
                        self.price_unit = 0

                    return {'domain': {'product_id': domain}}
                elif self.print_stamp_id.stamp_type == 'promotion':
                    line_ids = self.env['pos.promotion.qty.price'].search(
                        [('promotion_id', '=', self.print_stamp_id.promotion_id.id)])
                    ids = []
                    for line in line_ids:
                        ids.append(line.product_id.id)
                    if self.product_id:
                        self.uom_id = self.product_id.product_tmpl_id.uom_id.id
                        pricelist_item = self.env['product.pricelist.item'].sudo().search(
                            [('pricelist_id', '=', self.print_stamp_id.pricelist_id.id),
                             ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id), '|',('date_end','=',False),('date_end','>=',datetime.today()),
                             '|', ('date_start', '=', False), ('date_start', '<=', datetime.today())], limit=1)
                        if pricelist_item:
                            price_unit = pricelist_item.fixed_price
                        else:
                            price_unit = self.product_id.product_tmpl_id.list_price

                        self.price_unit = price_unit
                        self.packed_date = self.print_stamp_id.promotion_id.start_date
                        self.expire_date = self.print_stamp_id.promotion_id.end_date
                        for line in line_ids:
                            if line.product_id == self.product_id:
                                price = price_unit
                                if line.check_discount_price == 'price':
                                    price = price_unit - line.price_unit
                                elif line.check_discount_price == 'discount' and line.discount > 0:
                                    price = price_unit - price_unit * (line.discount / 100)
                                self.price_unit = price
                                self.note = line.note
                    else:
                        self.uom_id = None
                        self.price_unit = 0
                        self.note = None
                        self.packed_date = None
                        self.expire_date = None
                    domain = [('id', 'in', ids), ('product_tmpl_id', 'in', self.print_stamp_id.shop_id.product_ids.ids)]
                    return {'domain': {'product_id': domain}}

            elif not self.promotion_config_id:
                raise UserError(_('You have not selected shop! Please choose shop.'))


        except Exception as e:
            raise ValidationError(e)

    @api.onchange('packed_date')
    def _onchange_expire_date(self):
        try:
            if self.print_stamp_id.stamp_type in ('shelf', 'product'):
                if self.product_id and self.packed_date:
                    self.expire_date = self.packed_date + relativedelta(days=self.product_id.product_tmpl_id.x_expiry)
                else:
                    self.expire_date = None
        except Exception as e:
            raise ValidationError(e)

    @api.onchange('name_above')
    def _onchange_name_above(self):
        try:
            if self.print_stamp_id.stamp_type == 'other':
                if self.print_stamp_id.promotion_id:
                    self.packed_date = self.print_stamp_id.promotion_id.start_date
                    self.expire_date = self.print_stamp_id.promotion_id.end_date
                else:
                    self.packed_date = None
                    self.expire_date = None
        except Exception as e:
            raise ValidationError(e)
    
    @api.onchange('qty_printing')
    def _onchange_qty_printing(self):
        try:
            if self.qty_printing < 0:
                raise UserError(_("Print quantity must be greater than or equal to 0"))
        except Exception as e:
            raise ValidationError(e)
