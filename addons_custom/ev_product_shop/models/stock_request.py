# -*- coding: utf-8 -*-
import xlrd3
import base64

from odoo import models, _
from odoo.exceptions import ValidationError, UserError


class StockRequest(models.Model):
    _inherit = 'stock.request'

    def action_send(self):
        try:
            if self.type == 'transfer':
                pos_shop = self.env['pos.shop'].sudo().search([('warehouse_id', '=', self.warehouse_id.id)])
                product_ids = self.env['product.product'].search([('product_tmpl_id', 'in', pos_shop.product_ids.ids)])

                list_product_errors = []

                for line in self.line_ids:
                    if not self.warehouse_id.x_is_supply_warehouse:
                        if not line.product_id.product_tmpl_id.active:
                            list_product_errors.append(line.product_id.product_tmpl_id.name)
                            continue
                        if not line.product_id.product_tmpl_id.x_is_tools:
                            if line.product_id in product_ids:
                                if not line.product_id.product_tmpl_id.sale_ok:
                                    list_product_errors.append(line.product_id.product_tmpl_id.name)
                                if not line.product_id.product_tmpl_id.available_in_pos and line.product_id.product_tmpl_id.sale_ok:
                                    list_product_errors.append(line.product_id.product_tmpl_id.name)
                            else:
                                list_product_errors.append(line.product_id.product_tmpl_id.name)

                mess_error = ' , '.join([str(err) for err in list_product_errors])
                if len(mess_error) != 0:
                    raise UserError(_('Product can not send request : (%s)') % str(mess_error))

            return super(StockRequest, self).action_send()

        except Exception as e:
            raise ValidationError(e)

    def action_import_line(self):
        try:
            wb = xlrd3.open_workbook(file_contents=base64.decodestring(self.field_binary_import))
        except:
            raise UserError(_("File not found or in incorrect format. Please check the .xls or .xlsx file format"))
        try:
            data = base64.decodebytes(self.field_binary_import)
            excel = xlrd3.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)

            check_product = []
            check_price = []
            check_qty = []
            check_type = []
            lines = []
            for i in range(3, sheet.nrows):
                default_code = str(sheet.cell_value(i, 1)).split('.')[0]
                pos_shop = self.env['pos.shop'].sudo().search(
                    [('warehouse_id', '=', self.warehouse_id.id)])
                product_id = self.env['product.product'].search(
                    [('default_code', '=', default_code), ('active', '=', True)], limit=1)
                if not product_id:
                    check_product.append(i + 1)
                else:
                    if self.type == 'transfer':
                        if not self.warehouse_id.x_is_supply_warehouse:
                            if not product_id.product_tmpl_id.x_is_tools:
                                if product_id.product_tmpl_id in pos_shop.product_ids:
                                    if not product_id.product_tmpl_id.available_in_pos and product_id.product_tmpl_id.sale_ok:
                                        check_product.append(i + 1)
                                else:
                                    check_product.append(i + 1)
                    if product_id.product_tmpl_id.type == 'service':
                        check_type.append(i + 1)
                if self.type == 'other_input':
                    if float(sheet.cell_value(i, 4)):
                        if float(sheet.cell_value(i, 4)) <= 0:
                            check_price.append(i + 1)
                    else:
                        check_price.append(i + 1)
                if float(sheet.cell_value(i, 5)):
                    if float(sheet.cell_value(i, 5)) <= 0:
                        check_qty.append(i + 1)
                else:
                    check_qty.append(i + 1)
            product_error = ' , '.join([str(elem) for elem in check_product])
            price_error = ' , '.join([str(price) for price in check_price])
            qty_error = ' , '.join([str(qty) for qty in check_qty])
            type_error = ' , '.join([str(pr_type) for pr_type in check_type])
            mess_error = ''
            if check_product:
                mess_error += _('\nProduct does not exist in warehouse, line (%s)') % str(product_error)
            if check_qty:
                mess_error += _('\nQuantity must be greater than 0, line (%s)') % str(qty_error)
            if check_type:
                mess_error += _('\nNot service type, line (%s)') % str(type_error)
            if self.type == 'other_input':
                if check_price:
                    mess_error += _('\nPrice must be greater than 0, line (%s)') % str(price_error)
            if mess_error:
                raise UserError(mess_error)
            else:
                for i in range(3, sheet.nrows):
                    default_code = str(sheet.cell_value(i, 1)).split('.')[0]
                    product_id = self.env['product.product'].search([('default_code', '=', default_code)],
                                                                    limit=1)
                    price = sheet.cell_value(i, 4)
                    if self.type == 'other_input':
                        price = float(sheet.cell_value(i, 4))
                    note = sheet.cell_value(i, 6).strip()
                    if len(note) == 0:
                        note = None
                    for record in self:
                        check = False
                        if record.line_ids:
                            for rec in record.line_ids:
                                if rec.product_id.id == product_id.id:
                                    rec.qty += float(sheet.cell_value(i, 5))
                                    check = True
                        if not check:
                            argvs_request = (0, 0, {
                                'request_id': record.id,
                                'product_id': product_id.id,
                                'uom_id': product_id.product_tmpl_id.uom_id.id,
                                'price_unit': price,
                                'qty': float(sheet.cell_value(i, 5)),
                                'note': note,
                            })
                            lines.append(argvs_request)

            self.line_ids = lines
            self.field_binary_import = None
            self.field_binary_name = None

        except Exception as e:
            raise ValidationError(e)
