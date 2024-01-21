# -*- coding: utf-8 -*-
import base64
import datetime
import io

from odoo import models
from PIL import Image


class StockCardXLS(models.AbstractModel):
    _name = 'report.ev_cash_statement.cash_statement_xlsx'
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
            img_data = base64.b64decode(obj.company_id.logo)
            image = io.BytesIO(img_data)
            bound_width_height = (400, 200)
            image_data = self.get_resized_image_data(image, bound_width_height)
            im = Image.open(image_data)
            im.seek(0)

            address = 'Địa chỉ: '
            if obj.company_id.street:
                address = address + ' ' + obj.company_id.street
            if obj.company_id.street2:
                address = address + ' ' + obj.company_id.street2
            if obj.company_id.city:
                address = address + ' ' + obj.company_id.city
            if obj.company_id.state_id:
                address = address + ' ' + obj.company_id.state_id.name
            if obj.company_id.country_id:
                address = address + ' ' + obj.company_id.country_id.name

            format_tittle = workbook.add_format({'font_size': 10, 'align': 'top', 'bold': False})
            format1 = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': True})
            format2 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
            format3 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
            format4 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': False})
            format5 = workbook.add_format({'font_size': 12, 'align': 'right', 'bold': False})
            format6 = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True})
            format7 = workbook.add_format(
                {'num_format': 'dd-MM-yyyy HH:mm', 'font_size': 12, 'align': 'center', 'bold': True})
            border_format = workbook.add_format({
                'border': 1,
            })

            sheet = workbook.add_worksheet(obj.name)
            sheet.set_column(10, 10, 11)
            sheet.merge_range('A1:C5', '')
            sheet.insert_image('A1:C5', 'myimage.png', {'image_data': image_data})
            sheet.merge_range('D1:H1', obj.company_id.name, format1)
            sheet.merge_range('D2:H2', address, format2)
            sheet.merge_range('D3:H3', 'Bảng kiểm kê quỹ tiền mặt', format2)
            sheet.merge_range('D4:H4', obj.config_id.name, format2)
            sheet.merge_range('D5:H5', datetime.datetime.now(), format7)
            sheet.merge_range('I1:J5', 'Mã hiệu:', format_tittle)

            sheet.write('A6', 'STT', format3)
            sheet.merge_range('B6:C6', 'Mệnh giá(VNĐ)', format3)
            sheet.merge_range('D6:E6', 'Số lượng(tờ)', format3)
            sheet.merge_range('F6:H6', 'Thành tiền(VNĐ)', format3)
            sheet.merge_range('I6:J6', 'Ghi chú', format3)

            stt = 1
            x = 7
            amount_total = 0
            for record in obj.cash_statement_ids:
                amount = record.denominations * record.quantity
                sheet.write('A' + str(x), stt, format4)
                sheet.merge_range('B' + str(x) + ':' + 'C' + str(x), record.denominations, format4)
                sheet.merge_range('D' + str(x) + ':' + 'E' + str(x), record.quantity, format4)
                sheet.merge_range('F' + str(x) + ':' + 'H' + str(x), amount, format4)
                sheet.merge_range('I' + str(x) + ':' + 'J' + str(x), '')
                stt += 1
                x += 1
                amount_total += amount

            sheet.merge_range('A' + str(x) + ':' + 'E' + str(x), 'Tổng cộng:', format3)
            sheet.merge_range('F' + str(x) + ':' + 'H' + str(x), amount_total, format4)
            sheet.merge_range('I' + str(x) + ':' + 'J' + str(x), '')

            sheet.merge_range('A' + str(x + 1) + ':' + 'J' + str(x + 1), '')

            sheet.merge_range('A' + str(x + 2) + ':' + 'E' + str(x + 2), 'Số dư theo sổ quỹ trên phần mềm:', format6)
            sheet.merge_range('A' + str(x + 3) + ':' + 'E' + str(x + 3), 'Tổng số tiền thực tế kiểm đếm:', format6)
            sheet.merge_range('A' + str(x + 4) + ':' + 'E' + str(x + 4), 'Chênh lệch:', format6)

            sheet.merge_range('F' + str(x + 2) + ':' + 'H' + str(x + 2), obj.total_payments_amount, format4)
            sheet.merge_range('F' + str(x + 3) + ':' + 'H' + str(x + 3), amount_total, format4)
            sheet.merge_range('F' + str(x + 4) + ':' + 'H' + str(x + 4), amount_total - obj.total_payments_amount,
                              format4)

            sheet.merge_range('I' + str(x + 2) + ':' + 'J' + str(x + 2), 'VNĐ', format4)
            sheet.merge_range('I' + str(x + 3) + ':' + 'J' + str(x + 3), 'VNĐ', format4)
            sheet.merge_range('I' + str(x + 4) + ':' + 'J' + str(x + 4), 'VNĐ', format4)

            sheet.merge_range('A' + str(x + 5) + ':' + 'J' + str(x + 6), ',ngày......tháng......năm \n'
                                                                         '          Lập biểu', format4)
            sheet.conditional_format(0, 0, x + 5, x + 6, {'type': 'blanks', 'format': border_format})
