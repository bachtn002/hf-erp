import base64
import datetime
import io

from odoo import models
from PIL import Image


class MoveVoucherXLS(models.AbstractModel):
    _name = 'report.ev_pos_voucher.voucher_cost_control_xlsx'
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

            format0 = workbook.add_format({'font_size': 16, 'align': 'center', 'bold': False, 'border': True})
            format1 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True, 'border': True})
            format2 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': False, 'border': True})
            format3 = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': False, 'border': True})
            format4 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': False, 'border': True})
            format5 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': True, 'border': True})
            money = workbook.add_format({'num_format': '#,##0', 'align': 'right', 'border': True})
            border_format = workbook.add_format({
                'border': 1,
            })

            sheet = workbook.add_worksheet(obj.name)
            sheet.set_row(0, 20)
            sheet.set_row(2, 20)
            sheet.set_column(0, 0, 20)
            sheet.set_column(1, 2, 15)
            sheet.set_column(3, 3, 10)
            sheet.set_column(4, 4, 25)
            sheet.set_column(5, 5, 15)
            sheet.set_column(6, 8, 20)
            sheet.set_column(9, 9, 10)

            from_date = obj.from_date.strftime('%d/%m/%Y')
            to_date = obj.to_date.strftime('%d/%m/%Y')
            sheet.merge_range('A1:B3', '', border_format)
            sheet.insert_image('A1:B3', 'myimage.png', {'image_data': image_data})
            sheet.merge_range('C1:I1', obj.company_id.name, format0)
            sheet.merge_range('C2:I2', address, format2)
            sheet.merge_range('C3:I3', 'ĐỐI SOÁT CHI PHÍ VOUCHER', format3)
            sheet.merge_range('A4:B4', '', border_format)
            sheet.merge_range('E4:F4', '', border_format)
            sheet.write_rich_string('A4', 'Từ ngày: ', format4, from_date, format5)
            sheet.write_rich_string('E4', 'Đến ngày: ', format4, to_date, format5)
            sheet.write('A5', 'Phiếu mua hàng', format1)
            sheet.write('B5', 'Tên voucher', format1)
            sheet.write('C5', 'Ngày sử dụng', format1)
            sheet.write('D5', 'Giá trị', format1)
            sheet.write('E5', 'Đơn hàng', format1)
            sheet.write('F5', 'Thanh toán', format1)
            sheet.write('G5', 'Tài khoản chi phí', format1)
            sheet.write('H5', 'Bộ phận chịu phí', format1)
            sheet.write('I5', 'Khoản mục phí', format1)
            sheet.write('J5', 'Bút toán', format1)

            i = 6
            for line in obj.line_ids:
                used_date = line.used_date.strftime('%d/%m/%Y')
                sheet.write('A' + str(i), line.lot_id.name, format2)
                sheet.write('B' + str(i), line.product_id.product_tmpl_id.name, format2)
                sheet.write('C' + str(i), used_date, format2)
                sheet.write('D' + str(i), line.amount, money)
                sheet.write('E' + str(i), line.pos_order_id.name, format2)
                sheet.write('F' + str(i), line.pos_payment_id.amount, money)
                sheet.write('G' + str(i), line.account_id.name or '', format2)
                sheet.write('H' + str(i), line.analytic_account_id.name, format2)
                sheet.write('I' + str(i), line.account_expense_item_id.name or '', format2)
                sheet.write('J' + str(i), line.account_move_id.name or '', format2)
                i += 1
