# -*- coding: utf-8 -*-
import base64
import datetime

import xlrd

from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


class PromotionQtyPriceIMP(models.TransientModel):
    _name = 'promotion.qty.price.import'

    promotion_price_file = fields.Binary(string='Choose File')

    def import_promotion_price(self):
        try:
            wb = xlrd.open_workbook(file_contents=base64.decodestring(self.promotion_price_file))
        except:
            raise ValidationError(_('Import file must be an excel file'))
        data = base64.decodebytes(self.promotion_price_file)
        excel = xlrd.open_workbook(file_contents=data)
        sheet = excel.sheet_by_index(0)

        promotion_id = self.env['pos.promotion'].browse(self._context.get('active_id'))
        check_product = []
        check_qty = []
        check_price_unit = []
        check_discount = []
        check_type = []
        for i in range(1, sheet.nrows):
            try:
                default_code = str(sheet.cell_value(i, 0))
                default_code = default_code.replace('.0', '')
                product_id = self.env['product.product'].search([('default_code', '=', default_code)], limit=1)
            except:
                product_id = self.env['product.product'].search([('default_code', '=', sheet.cell_value(i, 0))],
                                                                limit=1)
            if not product_id:
                check_product.append(i + 1)
            # if float(sheet.cell_value(i, 1)):
            #     if float(sheet.cell_value(i, 1)) < 0:
            #         check_qty.append(i + 1)
            # else:
            #     check_qty.append(i + 1)

            # check type
            if len(str(sheet.cell_value(i, 2))) == 0:
                check_type.append(i + 1)
            if str(sheet.cell_value(i, 2)) != 'GG' and str(sheet.cell_value(i, 2)) != 'CK':
                check_type.append(i + 1)
            try:
                if float(int(sheet.cell_value(i, 3))):
                    if float(int(sheet.cell_value(i, 3))) <= 0:
                        check_price_unit.append(i + 1)
                else:
                    check_price_unit.append(i + 1)
            except:
                if str(sheet.cell_value(i, 2)) == 'GG':
                    check_price_unit.append(i + 1)

            # check discount
            try:
                if float(int(sheet.cell_value(i, 4))):
                    if float(int(sheet.cell_value(i, 4))) <= 0 or float(int(sheet.cell_value(i, 4))) > 100:
                        check_discount.append(i + 1)
                else:
                    check_discount.append(i + 1)
            except:
                if str(sheet.cell_value(i, 2)) == 'CK':
                    check_discount.append(i + 1)

        product_error = ' , '.join([str(product) for product in check_product])
        qty_error = ' , '.join([str(qty) for qty in check_qty])
        price_unit_error = ' , '.join([str(price_unit) for price_unit in check_price_unit])
        discount_error = ' , '.join([str(discount) for discount in check_discount])
        type_error = ' , '.join([str(type) for type in check_type])
        mess_error = ''
        if product_error:
            mess_error += _('\nProduct does not exist in the system, line (%s)') % str(product_error)
        if qty_error:
            mess_error += _('\nQuantity must be greater than 0, line (%s)') % str(qty_error)
        if price_unit_error:
            mess_error += _('\nPrice unit must be greater than 0, line (%s)') % str(price_unit_error)
        if discount_error:
            mess_error += _('\nDiscount must be greater than 0 and less 100, line (%s)') % str(discount_error)
        if type_error:
            mess_error += _('\nType must be CK or GG, line (%s)') % str(type_error)
        if mess_error:
            raise UserError(mess_error)
        else:
            promotion_id.pos_promotion_qty_price_ids.unlink()
            for i in range(1, sheet.nrows):
                check = False
                # product_id = self.env['product.product'].search([('default_code', '=', sheet.cell_value(i, 0))], limit=1)
                qty = self.check_qty(sheet.cell_value(i, 1))
                try:
                    default_code = str(sheet.cell_value(i, 0))
                    default_code = default_code.replace('.0', '')
                    product_id = self.env['product.product'].search(
                        [('default_code', '=', default_code)], limit=1)
                except:
                    product_id = self.env['product.product'].search([('default_code', '=', sheet.cell_value(i, 0))],
                                                                    limit=1)
                print('sheet.cell_value(i, 2)', sheet.cell_value(i, 2))
                if str(sheet.cell_value(i, 2)) == 'GG':
                    self.env['pos.promotion.qty.price'].create({
                        'promotion_id': promotion_id.id,
                        'product_id': product_id.id,
                        'check_discount_price':'price',
                        'qty': qty,
                        'price_unit': float(sheet.cell_value(i, 3)),
                        'note': (sheet.cell_value(i, 5)),
                    })
                    self.env.cr.commit()
                elif str(sheet.cell_value(i, 2)) == 'CK':
                    self.env['pos.promotion.qty.price'].create({
                        'promotion_id': promotion_id.id,
                        'product_id': product_id.id,
                        'check_discount_price':'discount',
                        'qty': qty,
                        'discount': float(sheet.cell_value(i, 4)),
                        'note': (sheet.cell_value(i, 5)),

                    })
                    self.env.cr.commit()

                # if promotion_id.pos_promotion_qty_price_ids:
                #     for record in promotion_id.pos_promotion_qty_price_ids:
                #             if record.product_id.id == product_id.id:
                #                 record.qty += float(sheet.cell_value(i, 1))
                #                 check = True
                # if check == False:
                #     self.env['pos.promotion.qty.price'].create({
                #         'promotion_id': promotion_id.id,
                #         'product_id': product_id.id,
                #         'qty':float(sheet.cell_value(i, 1)),
                #         'price_unit': float(sheet.cell_value(i, 2)),
                #     })
                #     self.env.cr.commit()
    def check_qty(self, qty):
        try:
            qty = float(qty)
            return qty
        except:
            return 0
