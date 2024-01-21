import base64

import xlrd3

from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError


class SaleRequestLineIMP(models.TransientModel):
    _inherit = 'import.xls.wizard.stock'

    def import_xls_stock(self):
        try:
            wb = xlrd3.open_workbook(file_contents=base64.decodestring(self.upload_file))
        except:
            raise UserError(_('Import file must be an excel file'))
        try:
            data = base64.decodebytes(self.upload_file)
            excel = xlrd3.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)

            sale_request_id = self.env['sale.request'].browse(self.env.context.get('active_id'))
            check_product = []
            check_qty = []
            check_type = []
            for i in range(6, sheet.nrows):
                default_code = str(sheet.cell_value(i, 0)).split('.')[0]
                pos_shop = self.env['pos.shop'].sudo().search(
                    [('warehouse_id', '=', sale_request_id.warehouse_id.id)])
                product_id = self.env['product.product'].search(
                    [('default_code', '=', default_code), ('active', '=', True)], limit=1)
                if not product_id:
                    check_product.append(i + 1)
                else:
                    if not sale_request_id.warehouse_id.x_is_supply_warehouse:
                        if product_id.product_tmpl_id in pos_shop.product_ids:
                            if not product_id.product_tmpl_id.x_is_tools:
                                if not product_id.product_tmpl_id.available_in_pos and product_id.product_tmpl_id.sale_ok:
                                    check_product.append(i + 1)
                        else:
                            if not product_id.product_tmpl_id.x_is_tools:
                                check_product.append(i + 1)
                    if product_id.product_tmpl_id.type == 'service':
                        check_type.append(i + 1)
                if float(sheet.cell_value(i, 2)) < 0:
                    check_qty.append(i + 1)
            product_error = ' , '.join([str(product) for product in check_product])
            qty_error = ' , '.join([str(qty) for qty in check_qty])
            type_error = ' , '.join([str(pr_type) for pr_type in check_type])
            mess_error = ''
            if check_product:
                mess_error += _('\nProduct does not exist in warehouse, line (%s)') % str(product_error)
            if check_qty:
                mess_error += _('\nQuantity must be greater than 0, line (%s)') % str(qty_error)
            if check_type:
                mess_error += _('\nNot service type, line (%s)') % str(type_error)

            if mess_error:
                raise UserError(mess_error)
            else:
                for line in sale_request_id.sale_request_line:
                    line.unlink()
                for i in range(6, sheet.nrows):
                    default_code = str(sheet.cell_value(i, 0)).split('.')[0]
                    product_id = self.env['product.product'].search([('default_code', '=', default_code)], limit=1).id
                    # shop_id = self.env['pos.shop'].sudo().search(
                    #     [('warehouse_id', '=', sale_request_id.warehouse_id.id)],
                    #     limit=1)
                    # predicted_qty = self.env['request.forecast'].sudo().search(
                    #     [('shop_id', '=', shop_id.id), ('product_id', '=', product_id),
                    #      ('date', '=', sale_request_id.date_request)], limit=1).predicted_qty
                    check_line = False
                    qty = float(sheet.cell_value(i, 2))
                    note = sheet.cell_value(i, 3).strip()
                    if len(note) == 0:
                        note = None
                    for line in sale_request_id.sale_request_line:
                        if line.product_id.id == product_id:
                            line.qty += qty
                            check_line = True
                    if not check_line:
                        self.env['sale.request.line'].create({
                            'sale_request_id': sale_request_id.id,
                            'product_id': product_id,
                            'qty': qty,
                            'note': note,
                        })
                        self.env.cr.commit()

        except Exception as e:
            raise ValidationError(e)
