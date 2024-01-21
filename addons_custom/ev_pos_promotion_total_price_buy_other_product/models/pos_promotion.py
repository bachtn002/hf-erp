# -*- coding: utf-8 -*-
import base64

import xlrd

from odoo.osv import osv
from odoo import models, fields, _, api
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError, UserError


class PosPromotion(models.Model):
    _inherit = 'pos.promotion'

    type = fields.Selection(selection_add=[
        ('total_price_buy_other_product', 'Giảm giá hàng hóa theo giá trị đơn hàng')
    ])
    pos_promotion_total_price_buy_other_product_ids = fields.One2many('pos.promotion.total.price.buy.other.product',
                                                                      'promotion_id',
                                                                      string="Promotion Total Price Buy Other Product")
    field_binary_import_promotion_total = fields.Binary(string="Field Binary Import")
    field_binary__promotion_total_name = fields.Char(string="Field Binary Name")

    def download_template_promotion_total_buy(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_pos_promotion_total_price_buy_other_product/static/template/mẫu phiếu import giảm giá hàng '
                   'hóa theo giá trị đơn hàng.xls',
            "target": "_parent",
        }

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    def action_import_line_promotion_total_buy(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise ValidationError(_(
                    "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodebytes(self.field_binary_import_promotion_total)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            data = self._get_data_from_sheet(sheet)
            checked_product_code = self.check_product_code(data)
            if not checked_product_code:
                raise ValidationError(
                    _("Product Code not exist. Please check those again.\n {}").format(checked_product_code))
            self._create_line_promotion_total_buy(data=data)

        except ValueError as e:
            raise osv.except_osv("Warning!", e)

    def _get_data_from_sheet(self, sheet):
        index = 1
        data = []
        while index < sheet.nrows:
            data_rows = []
            product_code = sheet.cell(index, 0).value  # 0
            quantity = sheet.cell(index, 1).value  # 1
            price = sheet.cell(index, 2).value  # 2
            discount = sheet.cell(index, 3).value  # 3
            total_price = sheet.cell(index, 4).value  # 4
            data_rows.append(product_code)
            data_rows.append(quantity)
            data_rows.append(price)
            data_rows.append(discount)
            data_rows.append(total_price)
            data.append(data_rows)
            index = index + 1
        return data

    def check_product_code(self, data):
        lots = []
        checks = []
        for data_product in data:
            product_id_import = self.env['product.product'].search(
                [('default_code', '=', data_product[0])]).id
            if product_id_import is False:
                checks.append(data_product[0])
        if len(checks) > 0:
            return False
        return True

    def _create_line_promotion_total_buy(self, data):
        for data_promotion in data:
            product_id = self.env['product.product'].search([('default_code', '=', data_promotion[0])]).id
            qty = data_promotion[1]
            price_unit = data_promotion[2]
            total_price = data_promotion[4]
            discount = data_promotion[3]
            check_discount_price = ''
            if price_unit:
                check_discount_price = 'price'
            elif discount:
                check_discount_price = 'discount'
            self.env['pos.promotion.total.price.buy.other.product'].create(
                {'promotion_id': self.id, 'product_id': product_id,
                 'qty': qty, 'price_unit': price_unit, 'total_price': total_price, 'discount': discount,
                 'check_discount_price': check_discount_price})
            self.env.cr.commit()

    @api.constrains('pos_promotion_total_price_buy_other_product_ids')
    def check_uom_line_pos_promotion_total_price_buy_other_product_ids(self):
        for line in self.pos_promotion_total_price_buy_other_product_ids:
            if line.qty <= 0:
                # raise ValidationError(_("The number of product must be greater than 0!!"))
                pass
            else:
                uom_qty = float_round(line.qty, precision_rounding=line.uom_id.rounding, rounding_method='HALF-UP')
                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                qty = float_round(line.qty, precision_digits=precision_digits, rounding_method='HALF-UP')
                if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
                    raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                                                  defined on the unit of measure "%s". Please change the quantity done or the \
                                                                  rounding precision of your unit of measure.') % (
                        line.product_id.display_name, line.uom_id.name))

    @api.onchange('type')
    def _onchange_type(self):
        res = super(PosPromotion, self)._onchange_type()
        if self.type != 'total_price_buy_other_product':
            self.pos_promotion_total_price_buy_other_product_ids = False
        return res
