import base64
import io
from builtins import print

from PIL.Image import Image
from PIL import Image
from xlrd3.timemachine import xrange

from odoo import models


class SaleRequestReport(models.AbstractModel):
    _name = 'report.general.request.report'
    _inherit = 'report.report_xlsx.abstract'

    def get_resized_image_data(self, file_path, bound_width_height):
        # get the image and resize it
        im = Image.open(file_path)
        im.thumbnail(bound_width_height, Image.ANTIALIAS)  # ANTIALIAS is important if shrinking

        # stuff the image data into a bytestream that excel can read
        im_bytes = io.BytesIO()
        im.save(im_bytes, format='PNG')
        return im_bytes

    def generate_xlsx_report(self, workbook, data, lines):
        for obj in lines:
            imgdata = base64.b64decode(obj.company_id.logo)
            image = io.BytesIO(imgdata)
            # One sheet by partner
            format1 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
            format2 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': False})
            format_tittle = workbook.add_format({'font_size': 10, 'align': 'top', 'bold': False})
            format6 = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True})
            format5 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False})
            format4 = workbook.add_format({'font_size': 10, 'bold': False})
            format3 = workbook.add_format({'font_size': 18, 'align': 'center', 'bold': False})
            format7 = workbook.add_format(
                {'num_format': 'd mmm yyyy', 'font_size': 10, 'align': 'left', 'bold': False})
            sheet = workbook.add_worksheet(obj.name)
            sheet.set_column(0, 2, 15)
            sheet.set_column(3, 8, 25)
            sheet.set_row(0, 25)
            sheet.set_row(1, 25)
            sheet.set_row(2, 25)

            bound_width_height = (240, 240)
            image_data = self.get_resized_image_data(image, bound_width_height)
            im = Image.open(image_data)
            im.seek(0)  # reset the "file" for excel to read it.

            sheet.merge_range('A1:C3', '')
            sheet.insert_image('A1:C3', 'myimage.png', {'image_data': image_data})
            sheet.merge_range('D1:H1', obj.company_id.name, format3)
            sheet.merge_range('D2:H2', obj.company_id.street, format2)
            sheet.merge_range('D3:H3', 'BẢNG TỔNG HỢP YÊU CẦU CUNG ỨNG HÀNG HÓA TỪ KHO TỔNG', format3)
            sheet.merge_range('I1:I3', 'Mã hiệu:', format_tittle)
            sheet.write('A5', 'Ngày yêu cầu:', format6)
            sheet.write('A7', 'Mã sản phẩm', format1)
            sheet.write('B7', 'Tên sản phẩm', format1)
            sheet.write('C7', 'Nhóm sản phẩm', format1)
            sheet.write('D7', 'Đơn vị tính', format1)

            warehouse_des_list = []
            for warehouse_des in obj.general_request_line:
                warehouse_des_list.append(warehouse_des.warehoue_des_id.id)

            count = 6
            stt = 1

            warehouse_ids = []
            for warehouse in obj.general_warehouse_group_ids.warehouse_ids:
                if warehouse.id in warehouse_des_list:
                    warehouse_ids.append(warehouse.id)
            warehouse_list = self.env['stock.warehouse'].search([('id', 'in', warehouse_ids)], order='code asc')
            dict_col_warehouse = {}
            for warehouse in warehouse_list:
                sheet.write(5, count, warehouse.code, format2)
                sheet.write(6, count, warehouse.name, format1)
                warehouse_des_id = warehouse.id
                dict_col_warehouse[warehouse_des_id] = count
                count += 1
                stt += 1
            sheet.write(6, 4, 'Tổng số lượng yêu cầu', format1)
            sheet.write(6, 5, 'Số lượng tồn kho', format1)

            sheet.merge_range('B5:I5', obj.date, format7)
            general_request_lines = obj.general_request_line
            row_num = 8
            row_num_qty = 7
            arr_default_code = []
            dict_row_default_code_same = {}
            dict_sum_qty_default_code = {}
            for general_request_line in general_request_lines:
                if not general_request_line.product_id.default_code in arr_default_code:
                    sheet.write('A' + str(row_num), general_request_line.product_id.default_code, format2)
                    sheet.write('B' + str(row_num), general_request_line.product_id.name, format2)
                    sheet.write('C' + str(row_num), general_request_line.product_id.product_tmpl_id.categ_id.name,
                                format2)
                    sheet.write('D' + str(row_num), general_request_line.product_uom.name, format2)
                    dict_row_default_code_same[general_request_line.product_id.default_code] = row_num_qty
                    col_warehouse = dict_col_warehouse[general_request_line.warehoue_des_id.id]
                    sheet.write(row_num_qty, col_warehouse, general_request_line.qty, format2)
                    dict_sum_qty_default_code[
                        general_request_line.product_id.default_code] = general_request_line.qty
                    warehouse_des_list.append(general_request_line.warehoue_des_id.id)
                    row_num += 1
                    row_num_qty += 1
                else:
                    dict_sum_qty_default_code[
                        general_request_line.product_id.default_code] += general_request_line.qty
                    row_num_same_defaultcode = dict_row_default_code_same[
                        general_request_line.product_id.default_code]
                    col_warehouse = dict_col_warehouse[general_request_line.warehoue_des_id.id]
                    sheet.write(row_num_same_defaultcode, col_warehouse, general_request_line.qty, format2)

                arr_default_code.append(general_request_line.product_id.default_code)

            arr_default_code_no_duppicate = []
            for general_request_line in general_request_lines:
                if general_request_line.product_id.default_code not in arr_default_code_no_duppicate:
                    arr_default_code_no_duppicate.append(general_request_line.product_id.default_code)

            # tính tổng số lượng yêu cầu
            for code in arr_default_code_no_duppicate:
                sheet.write(dict_row_default_code_same[code], 4, dict_sum_qty_default_code[code],
                            format2)

            # tính số lượng tồn kho
            dict_stock_quant_code = {}
            for code in arr_default_code_no_duppicate:
                product_id = self.env['product.product'].search([('default_code', '=', code), ('active', '=', True)],
                                                                limit=1)
                quantity = self.env['stock.quant']._get_available_quantity(product_id, obj.warehouse_id.lot_stock_id)
                dict_stock_quant_code[code] = quantity
            for code in arr_default_code:
                sheet.write(dict_row_default_code_same[code], 5, dict_stock_quant_code[code],
                            format2)
            border_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'font_size': 10
            })

            col_ware = len(warehouse_des_list) + 5
            sheet.set_column(3, col_ware, 25)
            sheet.merge_range('F' + str(row_num_qty + 1) + ':' + 'I' + str(row_num_qty + 1),
                              'Hà Nội, ngày……..tháng…….năm………..',
                              format2)
            sheet.merge_range('F' + str(row_num_qty + 2) + ':' + 'I' + str(row_num_qty + 2), 'Lập phiếu',
                              format2)
            sheet.conditional_format(0, 0, row_num_qty - 1, col_ware,
                                     {'type': 'no_blanks', 'format': border_format})
            sheet.conditional_format(0, 0, row_num_qty - 1, col_ware,
                                     {'type': 'blanks', 'format': border_format})
