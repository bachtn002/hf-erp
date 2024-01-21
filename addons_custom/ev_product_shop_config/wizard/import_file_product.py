import base64

import xlrd3

from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError


class ImportFileProduct(models.TransientModel):
    _name = 'import.xls.wizard.product'

    upload_file = fields.Binary(string="Upload File")
    file_name = fields.Char(string="File Name")
    
    def import_xls_product(self):
        try:
            wb = xlrd3.open_workbook(file_contents=base64.decodestring(self.upload_file))
        except:
            raise UserError(_('Import file must be an excel file'))
        try:
            data = base64.decodebytes(self.upload_file)
            excel = xlrd3.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)

            pos_shop_id = self.env['pos.shop'].browse(self.env.context.get('active_id'))
            print(pos_shop_id)

            check_product = []
            product_ids = []
            for i in range(1, sheet.nrows):
                default_code = sheet.cell_value(i, 0)
                product_id = self.env['product.template'].search([('default_code', '=', default_code),('available_in_pos','=',True)], limit=1)
                if not product_id or not product_id.active:
                    check_product.append(i + 1)
                product_ids.append(product_id.id)
            product_error = ' , '.join([str(product) for product in check_product])
            mess_error = ''
            if check_product:
                mess_error += _('\nProduct does not exist in the system, line (%s)') % str(product_error)
            if mess_error:
                raise UserError(mess_error)
            else:
                product_tmpl_ids = self.env['product.template'].search([('id', 'in', product_ids)])
                pos_shop_id.product_ids = product_tmpl_ids

        except Exception as e:
            raise ValidationError(e)
