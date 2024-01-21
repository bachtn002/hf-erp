import base64

import xlrd3

from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import osv


class SupplyWarehouseGroupIMP(models.TransientModel):
    _name = 'supply.warehouse.group.import'

    upload_file = fields.Binary(string="Upload File")

    def import_supply_warehouse_group(self):
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

            check_warehouse = []
            for i in range(1, sheet.nrows):
                warehouse_id = self.env['stock.warehouse'].search([('code', '=', sheet.cell_value(i, 0))], limit = 1)
                if not warehouse_id:
                    check_warehouse.append(i + 1)

                list_check_warehouse = ' , '.join([str(id) for id in check_warehouse])
                mess_error = ''
                if list_check_warehouse:
                    mess_error += _('\nWarehouse not exist in the system, line (%s)') % str(
                        list_check_warehouse)
                if mess_error:
                    raise UserError(mess_error)
            else:
                supply_warehouse_group_id = self.env['supply.warehouse.group'].browse(self._context.get('active_id'))
                warehouse_ids = []
                for i in range(1, sheet.nrows):
                    warehouse_id = self.env['stock.warehouse'].search([('code', '=', sheet.cell_value(i, 0))], limit = 1)
                    if warehouse_id:
                        warehouse_ids.append(warehouse_id.id)
                list_warehouse = self.env['stock.warehouse'].search([('id', 'in', warehouse_ids)])
                supply_warehouse_group_id.warehouse_ids = list_warehouse

        except Exception as e:
            raise ValidationError(e)
