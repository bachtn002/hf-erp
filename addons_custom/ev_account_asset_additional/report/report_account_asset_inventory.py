import base64
import io

from PIL.Image import Image
from PIL import Image
from odoo import models
from datetime import datetime, timedelta
from xlsxwriter.utility import xl_rowcol_to_cell


class ReportAccountAssetInventory(models.AbstractModel):
    _name = 'report.ev_account_asset_additional.report_asset_inventory'
    _inherit = 'report.report_xlsx.abstract'

    def get_resized_image_data(self, file_path, bound_width_height):
        # get the image and resize it
        im = Image.open(file_path)
        im.thumbnail(bound_width_height, Image.ANTIALIAS)
        im_bytes = io.BytesIO()
        im.save(im_bytes, format='PNG')
        return im_bytes

    def generate_xlsx_report(self, workbook, data, inventory_lines):
        editable = workbook.add_format({'bold': True, 'border': 1})
        no_bold = workbook.add_format({'bold': False, 'border': 1})
        editable.set_align('center')
        editable.set_align('vcenter')
        no_bold.set_align('center')
        no_bold.set_align('vcenter')

        format0 = workbook.add_format(
            {'font_name': 'Times New Roman', 'font_size': 12, 'align': 'center', 'valign': 'vcenter', 'bold': True,
             'bottom': 2})
        format3 = workbook.add_format(
            {'font_name': 'Times New Roman', 'font_size': 18, 'align': 'center', 'bold': True})
        format1 = workbook.add_format(
            {'font_name': 'Times New Roman', 'font_size': 9, 'align': 'center', 'valign': 'vcenter', 'bold': True,
             'border': 1})
        format2 = workbook.add_format(
            {'font_name': 'Times New Roman', 'font_size': 9, 'align': 'center', 'bold': False, 'border': 1})

        format4 = workbook.add_format(
            {'font_name': 'Times New Roman', 'font_size': 14, 'align': 'left', 'bold': True, })
        format5 = workbook.add_format(
            {'font_name': 'Times New Roman', 'font_size': 14, 'align': 'left', 'bold': False, })
        format6 = workbook.add_format(
            {'font_name': 'Times New Roman', 'font_size': 11, 'align': 'left', 'bold': True, })

        ws = workbook.add_worksheet("Biên bản kiểm kê")
        # ws.insert_image('A1:C3', 'myimage.png', {'image_data': image_data})

        company = self.env['res.company'].sudo().search([('id', '=', 1)])
        imgdata = base64.b64decode(company.logo)
        image = io.BytesIO(imgdata)

        bound_width_height = (150, 120)
        image_data = self.get_resized_image_data(image, bound_width_height)
        im = Image.open(image_data)
        im.seek(0)

        ws.insert_image('A1:B1', 'myimage.png', {'image_data': image_data})

        ws.merge_range('A1:G1', company.name.upper(), format0)
        # ws.write('H1', 'BM.TCKT10 Ngày ban hành: Lần sửa đổi:')
        ws.set_row(0, 43.5)
        ws.merge_range('A3:H3', 'BIÊN BẢN KIỂM KÊ TÀI SẢN', format3)
        ws.set_row(2, 31)
        ws.merge_range('A4:F4', 'Hôm nay, ngày ........................ tại ........................ chúng tôi gồm có:',
                       format5)
        ws.set_row(3, 27)
        ws.merge_range('A5:F5', 'I. Ban kiểm kê gồm:', format4)
        ws.set_row(4, 18.75)
        ws.merge_range('A6:F6', '- Ông/Bà .................... Chức vụ: Trưởng ban kiểm kê', format5)
        ws.set_row(5, 18.75)
        ws.merge_range('A7:F7', '- Ông/Bà .................... Chức vụ: Ủy viên', format5)
        ws.set_row(6, 18.75)
        ws.merge_range('A8:F8', '- Ông/Bà .................... Chức vụ: Ủy viên', format5)
        ws.set_row(7, 18.75)
        ws.merge_range('A9:F9', 'II. Đơn vị quản lý, sử dụng tài sản: ........................ ', format4)
        ws.set_row(8, 18.75)
        ws.merge_range('A10:F10', '- Ông/Bà ........................ Chức vụ: .................... ', format5)
        ws.set_row(9, 18.75)
        ws.merge_range('A11:F11', '- Ông/Bà ........................ Chức vụ: .................... ', format5)
        ws.set_row(10, 18.75)
        ws.write('A12', 'Đã tiến hành kiểm kê tài sản, trang thiết bị, công cụ dụng cụ với kết quả như sau:', format5)
        ws.set_row(11, 27)

        ws.merge_range('A13:A14', u'STT', format1)
        ws.merge_range('B13:B14', u'Mã TS', format1)
        ws.merge_range('C13:C14', u'Tên TS', format1)
        ws.merge_range('D13:D14', u'Đơn vị tính', format1)
        ws.merge_range('H13:H14', u"Tình trạng", format1)
        ws.merge_range('I13:I14', u"Ghi chú", format1)
        ws.merge_range('E13:G13', 'Số lượng', format1)
        ws.write(13, 4, u'Theo sổ sách', format1)
        ws.write(13, 5, u'Thực tế', format1)
        ws.write(13, 6, u'Chênh lệch', format1)

        ws.set_column(0, 0, 10)
        ws.set_column(1, 1, 15)
        ws.set_column(2, 2, 53)
        ws.set_column(3, 3, 10)
        ws.set_column(4, 4, 10)
        ws.set_column(5, 5, 10)
        ws.set_column(6, 6, 25)
        ws.set_column(7, 7, 25)

        ws.set_row(13, 30.75)
        index = 1
        row = 14

        for line in inventory_lines.lines:
            if line.asset_id.state == 'draft':
                state = 'Dự thảo'
            elif line.asset_id.state == 'open':
                state = 'Đang chạy'
            elif line.asset_id.state == 'paused':
                state = 'Tạm dừng'
            elif line.asset_id.state == 'close':
                state = 'Đã đóng'
            else:
                state = ''
            uom = ''
            if line.asset_id.x_product_asset_id:
                uom = line.asset_id.x_product_asset_id.uom_id.name

            ws.write(row, 0, index, format2)
            ws.write(row, 1, line.asset_id.x_code, format2)
            ws.write(row, 2, line.asset_id.name, format2)
            ws.write(row, 3, uom, format2)
            ws.write(row, 4, line.quantity, format2)
            ws.write(row, 5, line.actual_quantity, format2)
            ws.write(row, 6, (line.actual_quantity - line.quantity), format2)
            ws.write(row, 7, state, format2)
            ws.write(row, 8, line.note, format2)
            index += 1
            row += 1
        for line in inventory_lines.additional_lines:
            if line:
                ws.write(row, 0, index, format2)
                ws.write(row, 1, line.code, format2)
                ws.write(row, 2, line.name, format2)
                ws.write(row, 3, line.unit, format2)
                ws.write(row, 4, '', format2)
                ws.write(row, 5, line.quantity if line.quantity else "", format2)
                ws.write(row, 6, line.quantity if line.quantity else "", format2)
                ws.write(row, 7, '', format2)
                ws.write(row, 8, line.note if line.note else "", format2)
                index += 1
                row += 1

        ws.write(row + 2, 2, 'Ban kiểm kê', format6)
        ws.write(row + 2, 5, 'Cửa hàng trưởng/Trưởng bộ phận', format6)
