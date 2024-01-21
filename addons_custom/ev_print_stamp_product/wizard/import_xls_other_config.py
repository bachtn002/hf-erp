import base64
from datetime import datetime
from pickle import NONE

import xlrd3

from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError


class ImportXlsOtherConfig(models.TransientModel):
    _name = 'import.xls.other.config'

    upload_file = fields.Binary(string="Upload File")
    file_name = fields.Char(string="File Name")

    def import_xls_other_config(self):
        try:
            wb = xlrd3.open_workbook(file_contents=base64.decodestring(self.upload_file))
        except:
            raise UserError(_('Import file must be an excel file'))
        try:
            data = base64.decodebytes(self.upload_file)
            excel = xlrd3.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)

            # check_uom = []
            check_price = []
            check_date = []
            for i in range(2,sheet.nrows):
                other_config_id = self.env['product.other.config'].browse(self.env.context.get('active_id'))

                # uom_error = ' , '.join([str(uom) for uom in check_uom])
                if float(sheet.cell_value(i, 3)) < 0 or float(sheet.cell_value(i, 4)) < 0:
                    check_price.append(i + 1)
                if (sheet.cell_value(i, 5)) == "" or (sheet.cell_value(i, 6)) == "":
                    check_date.append(i+1)
                    print("Check date")
                    print(check_date)
            price_error = ' , '.join([str(price) for price in check_price])
            date_error = ' , '.join([str(date) for date in check_date])
            mess_error = ''
            if check_price:
                mess_error += _('\nPrice must be greater than 0, line (%s)') % str(price_error)
            if check_date:
                mess_error += _('\nDate cannot be empty, line (%s)') % str(date_error)
                # if check_uom:
                #     mess_error += _('Uom does not exist in the system, line (%s)') % str(check_uom)
            if mess_error:
                raise UserError(mess_error)
            else:
                for i in range(2,sheet.nrows):
                    uom_id = self.env['uom.uom'].search([('name', 'ilike', (sheet.cell_value(i, 2)))], limit=1)
                    vals = {
                        'other_config_id': other_config_id.id,
                        'name_above': sheet.cell_value(i, 0),
                        'name_below': sheet.cell_value(i, 1),
                        'uom_id': uom_id.id,
                        'price_unit_before': sheet.cell_value(i, 3),
                        'price_unit': sheet.cell_value(i, 4),
                        'packed_date': datetime.strptime((sheet.cell_value(i, 5)), '%d/%m/%Y'),
                        'expire_date': datetime.strptime((sheet.cell_value(i, 6)), '%d/%m/%Y'),  
                        'note':sheet.cell_value(i, 7),  
                    }
                    # print(vals)
                    self.env['product.other.config.line'].create(vals)

        except Exception as e:
            raise ValidationError(e)
