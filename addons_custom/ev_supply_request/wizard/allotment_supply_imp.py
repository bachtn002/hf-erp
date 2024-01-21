import base64

import xlrd3

from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import osv


class AllotmentSupplyIMP(models.TransientModel):
    _name = 'allotment.supply.import'

    upload_file = fields.Binary(string="Upload File")

    def _is_number(self, name):
        try:
            float(name)
            return True
        except ValueError:
            return False

    def import_allotment_supply(self):
        try:
            try:
                data = base64.decodebytes(self.upload_file)
                wb = xlrd3.open_workbook(file_contents=data)
            except:
                raise ValidationError(
                    _("File not found or in incorrect format. Please check the .xls or .xlsx file format")
                )
            data = base64.decodestring(self.upload_file)
            excel = xlrd3.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 5
            arr_line_error_not_exist_database = []
            warehouse_not_exist_database = []
            allotment_supply_obj = self.env['allotment.request'].browse(self._context.get('active_id'))
            while index < sheet.nrows:
                warehouse_code = sheet.cell(index, 0).value
                if warehouse_code == '':
                    break
                warehouse_code = str(warehouse_code).upper()
                warehouse_obj = self.env['stock.warehouse'].search([('code', '=', warehouse_code)], limit=1)
                if not warehouse_obj:
                    warehouse_not_exist_database.append(index + 1)
                listToStr_warehouse_not_exist_database = ' , '.join(
                    [str(elem) for elem in warehouse_not_exist_database])
                if len(warehouse_not_exist_database) != 0:
                    raise ValidationError(
                        _('Kho không tồn tại trong hệ thống, dòng (%s)') % str(listToStr_warehouse_not_exist_database))
                product_code = sheet.cell(index, 2).value
                if self._is_number(product_code):
                    product_code = str(product_code).split('.')[0]
                else:
                    product_code = str(product_code).upper()
                product_obj = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                if not product_obj:
                    arr_line_error_not_exist_database.append(index + 1)
                listToStr_line_not_exist_database = ' , '.join(
                    [str(elem) for elem in arr_line_error_not_exist_database])
                if len(arr_line_error_not_exist_database) != 0:
                    raise ValidationError(
                        _('Product is not exists, line (%s)') % str(listToStr_line_not_exist_database))
                uom_name = sheet.cell(index, 4).value
                uom_obj = self.env['uom.uom'].search([('name', '=', uom_name)], limit=1)
                if not uom_obj:
                    raise UserError(_('Không tồn tại đơn vị tính' + str(uom_name)))
                partner_code = sheet.cell(index, 5).value
                partner_obj = self.env['res.partner'].search([('ref', '=', partner_code)], limit=1)
                if not partner_obj:
                    raise UserError(_('Không tồn tại NCC tại dòng ' + str(index + 1)))
                qty = sheet.cell(index, 6).value
                price_unit = sheet.cell(index, 7).value
                if product_obj and warehouse_obj and uom_obj:
                    if product_obj.uom_po_id.category_id.id != uom_obj.category_id.id:
                        raise UserError(_('Đơn vị tính khác nhóm cấu hình trong sản phẩm' + str(uom_name)))
                    line_obj = self.env['allotment.supply.line'].search(
                        [('allotment_supply_id', '=', allotment_supply_obj.id),
                         ['product_id', '=', product_obj.id],
                         ['warehouse_dest_id', '=', warehouse_obj.id]],
                        limit=1)
                    if line_obj:
                        line_obj.qty_buy = qty
                        if self._is_number(price_unit):
                            if price_unit > 0:
                                line_obj.price_unit = price_unit
                            else:
                                raise UserError(_('Price unit must be greater than 0, line (%s)', index))
                        else:
                            raise UserError(_('Invalid price unit, line (%s)', str(index)))
                        line_obj.uom_id = uom_obj.id
                        if partner_obj:
                            line_obj.partner_id = partner_obj.id
                index = index + 1
        except Exception as e:
            raise ValidationError(e)
