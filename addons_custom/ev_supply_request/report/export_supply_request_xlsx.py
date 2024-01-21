from odoo import models
from datetime import datetime, timedelta
from xlsxwriter.utility import xl_rowcol_to_cell
import base64
import io
from PIL.Image import Image
from PIL import Image


class ExportSupplyRequest(models.AbstractModel):
    _name = 'report.ev_supply_request.export_supply_request'
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
            # One sheet by partner
            imgdata = base64.b64decode(obj.company_id.logo)
            image = io.BytesIO(imgdata)
            format1 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
            format2 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': False})
            format_tittle = workbook.add_format({'font_size': 10, 'align': 'top', 'bold': False})
            format6 = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': False})
            format5 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False})
            format4 = workbook.add_format({'font_size': 10, 'bold': False})
            format3 = workbook.add_format({'font_size': 18, 'align': 'center', 'bold': False})
            format7 = workbook.add_format(
                {'num_format': 'mmm d yyyy hh:mm AM/PM', 'font_size': 10, 'align': 'left', 'bold': False})
            sheet = workbook.add_worksheet(obj.name)
            sheet.set_column(0, 2, 15)
            sheet.set_column(3, 9, 25)
            sheet.set_row(0, 25)
            sheet.set_row(1, 25)
            sheet.set_row(2, 25)

            bound_width_height = (240, 240)

            image_data = self.get_resized_image_data(image, bound_width_height)
            im = Image.open(image_data)
            # im.show()  # test if it worked so far - it does for me
            im.seek(0)

            sheet.merge_range('A1:B3', '')
            sheet.insert_image('A1:C3', 'myimage.png', {'image_data': image_data})
            sheet.merge_range('C1:H1', lines.company_id.name, format3)
            sheet.merge_range('C2:H2', lines.company_id.street, format2)
            sheet.merge_range('C3:H3', 'BẢNG TỔNG HỢP YÊU CẦU MUA HÀNG', format3)
            sheet.merge_range('I1:J3', 'Mã hiệu:', format_tittle)
            sheet.merge_range('A4:I4', 'Ngày đặt hàng:' + str(obj.date), format7)
            sheet.write('A5', 'Mã Cửa Hàng/Kho tổng:', format2)
            sheet.write('B5', 'Tên cửa hàng', format2)
            sheet.write('C5', 'Địa chỉ', format2)
            sheet.write('D5', 'Mã sản phẩm:', format2)
            sheet.write('E5', 'Tên sản phẩm', format2)
            sheet.write('F5', 'Đơn vị đặt hàng(ĐVT)', format2)
            sheet.write('G5', 'Mã NCC', format2)
            sheet.write('H5', 'Số lượng yêu cầu', format2)
            sheet.write('I5', 'Nhóm hàng hóa', format2)
            sheet.write('J5', 'Ghi chú', format2)

            index = 6
            for line in obj.line_ids:
                sheet.write('A' + str(index), line.warehouse_dest_id.code, format6)
                sheet.write('B' + str(index), line.warehouse_dest_id.name, format6)
                sheet.write('C' + str(index),
                            line.warehouse_dest_id.x_address_warehouse if line.warehouse_dest_id.x_address_warehouse else '',
                            format6)
                sheet.write('D' + str(index), line.product_id.default_code, format6)
                sheet.write('E' + str(index), line.product_id.name, format6)
                sheet.write('F' + str(index), line.product_id.uom_po_id.name, format6)
                sheet.write('G' + str(index), line.partner_id.ref if line.partner_id else '', format6)
                sheet.write('H' + str(index), line.qty_request, format5)
                sheet.write('I' + str(index), line.product_id.categ_id.name, format6)
                sheet.write('J' + str(index), line.note if line.note else '', format6)
                index += 1

            border_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'font_size': 10
            })
            sheet.merge_range('F' + str(index + 2) + ':' + 'H' + str(index + 2),
                              'Hà Nội, ngày……..tháng…….năm………..',
                              format2)
            sheet.merge_range('F' + str(index + 3) + ':' + 'H' + str(index + 3), 'Lập phiếu',
                              format2)
            sheet.conditional_format(0, 0, index, 9,
                                     {'type': 'no_blanks', 'format': border_format})
            sheet.conditional_format(0, 0, index, 9,
                                     {'type': 'blanks', 'format': border_format})
