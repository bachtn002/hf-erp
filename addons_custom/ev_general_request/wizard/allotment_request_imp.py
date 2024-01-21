import base64

import xlrd3

from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import osv


class AllotmentRequestIMP(models.TransientModel):
    _name = 'allotment.request.import'

    upload_file = fields.Binary(string="Upload File")

    # hàm tìm allotment request line ứng với mã code sp và kho yêu cầu
    def find_allotment_request_line_with_code_stock(self, id, code, warehouse_des, qty_supply):
        allotment_request_obj = self.env['allotment.request'].search([('id', '=', id)])
        allotment_request_lines_obj = self.env['allotment.request.line'].search(
            [('allotment_request_id', '=', allotment_request_obj.id)])
        product_id = self.env['product.product'].search([('default_code', '=', code)]).id
        warehouse_des_id = self.env['stock.warehouse'].search([('code', '=', warehouse_des)]).id
        for allotment_request_line in allotment_request_lines_obj:
            if allotment_request_line.product_id.id == product_id and allotment_request_line.warehoue_des_id.id == warehouse_des_id:
                allotment_request_line.write({'qty_apply': qty_supply})

    def import_allotment_request(self):
        try:
            # wb = xlrd.open_workbook(file_contents=base64.decodebytes(self.upload_file))
            data = base64.decodebytes(self.upload_file)
            wb = xlrd3.open_workbook(file_contents=data)
            # wb = xlrd.open_workbook(self.upload_file)
        except:
            raise ValidationError(
                _("File not found or in incorrect format. Please check the .xls or .xlsx file format")
            )
        try:
            values = []
            for sheet in wb.sheets():
                for row in range(sheet.nrows):
                    col_values = []
                    for col in range(sheet.ncols):
                        value = sheet.cell(row, col).value
                        try:
                            value = str(value)
                        except:
                            pass
                        col_values.append(value)
                    values.append(col_values)

            allotment_request_obj = self.env['allotment.request'].browse(self._context.get('active_id'))
            warehouse_list = self.env['warehouse.supply'].search(
                [('warehoue_source_id', '=', allotment_request_obj.general_request_id.warehouse_id.id)])
            arr_warehouse_des = []
            # tạo mảng lưu mã kho yêu trong phiếu tổng hợp
            for warehouse in warehouse_list:
                if warehouse.warehoue_des_id.code not in arr_warehouse_des:
                    arr_warehouse_des.append(warehouse.warehoue_des_id.code)

            # kiểm tra mã cửa hàng có trong danh sách yêu cầu của kho tổng hợp không
            # for val_in_line in values[5]:
            #     if val_in_line != '' and val_in_line not in arr_warehouse_des:
            #         raise UserError(
            #             _("No stock in general request with code {0} exists. Please check the line : 5"))

            # kiểm tra mã sản phẩm có trong hệ thống hay không
            line_exist_code_product = 6
            for val in values[6:]:
                if val[0] != '':
                    line_exist_code_product += 1
            line_check_exist_data = 7
            arr_line_error_not_exist_database = []
            for val in values[7:line_exist_code_product]:
                product_id_import = self.env['product.product'].search(
                    [('default_code', '=', val[0])]).id
                if product_id_import is False:
                    arr_line_error_not_exist_database.append(line_check_exist_data)
                line_check_exist_data += 1
            listToStr_line_not_exist_database = ' , '.join([str(elem) for elem in arr_line_error_not_exist_database])
            if len(arr_line_error_not_exist_database) != 0:
                raise ValidationError(
                    _('Sản phẩm không tồn tại trong hệ thống, dòng (%s)') % str(listToStr_line_not_exist_database))

            # xác định kho ứng với cột trong excel
            col_stock = 6
            for val in values[5][6:]:
                if val != '':
                    col_stock += 1
            dict_stock_in_excel = {}
            col = 6
            for val in values[5][6:col_stock]:
                dict_stock_in_excel[val] = col
                col += 1
            for val in values[7:line_exist_code_product]:
                for t in dict_stock_in_excel:
                    if val[dict_stock_in_excel[t]] != '':
                        print(val[dict_stock_in_excel[t]])
                        self.find_allotment_request_line_with_code_stock(allotment_request_obj.id, val[0], t,
                                                                         val[dict_stock_in_excel[t]])

            obj_general_request = self.env['general.request'].search(
                [('id', '=', allotment_request_obj.general_request_id.id)])
            for rc in obj_general_request.general_request_line:
                obj_sale_request = self.env['sale.request.line'].search(
                    [('sale_request_id', '=', rc.request_line_id), ('product_id', '=', rc.product_id.id)])
                obj_sale_request.write({'qty_apply': rc.qty_apply})

        except Exception as e:
            raise ValidationError(e)
