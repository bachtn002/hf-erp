import base64

import xlrd3

from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import osv


class GeneralProductGroupIMP(models.TransientModel):
    _name = 'general.product.group.import'

    upload_file = fields.Binary(string="Upload File")

    def import_general_product_group(self):
        try:
            data = base64.decodebytes(self.upload_file)
            wb = xlrd3.open_workbook(file_contents=data)
        except:
            raise ValidationError(
                _("File not found or in incorrect format. Please check the .xls or .xlsx file format")
            )
        try:
            data = base64.decodebytes(self.upload_file)
            excel = xlrd3.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)

            check_product = []
            for i in range(1, sheet.nrows):
                product_id = self.env['product.product'].search(['|', ('default_code', '=', sheet.cell_value(i, 0)),
                                                                 ('barcode', '=', sheet.cell_value(i, 0))], limit=1)
                if not product_id or not product_id.active or product_id.type != 'product':
                    check_product.append(i + 1)

            list_check_product = ' , '.join([str(id) for id in check_product])
            mess_error = ''
            if list_check_product:
                mess_error += _('\nProduct not exist in the system or not active, line (%s)') % str(list_check_product)
            if mess_error:
                raise UserError(mess_error)
            else:
                general_product_group_id = self.env['general.product.group'].browse(self._context.get('active_id'))
                product_ids = []
                for i in range(1, sheet.nrows):
                    product_id = self.env['product.product'].search(['|', ('default_code', '=', sheet.cell_value(i, 0)),
                                                                     ('barcode', '=', sheet.cell_value(i, 0))], limit=1)
                    if product_id:
                        product_ids.append(product_id.id)
                list_product = self.env['product.product'].search([('id', 'in', product_ids)])
                general_product_group_id.product_ids = list_product

        except Exception as e:
            raise ValidationError(e)
