# -*- coding: utf-8 -*-
import base64

import io

from odoo import models
from PIL import Image


class StockCardXLS(models.AbstractModel):
    _name = 'report.ev_stock_card.stock_card_xlsx'
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
            bound_width_height = (240, 240)
            # image_path = 'myimage.png'
            image_data = self.get_resized_image_data(image, bound_width_height)
            im = Image.open(image_data)
            # im.show()  # test if it worked so far - it does for me
            im.seek(0)  # reset the "file" for excel to read it.

            context = self._context
            current_uid = context.get('uid')

            user = self.env['res.users'].browse(current_uid)

            # One sheet by partner
            format1 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
            format2 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': False})
            format_tittle = workbook.add_format({'font_size': 10, 'align': 'top', 'bold': False})
            format6 = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': False})
            format5 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False})
            format4 = workbook.add_format({'font_size': 10, 'bold': False})
            format3 = workbook.add_format({'font_size': 18, 'align': 'center', 'bold': False})
            format7 = workbook.add_format(
                {'num_format': 'd/mmm/yyyy', 'font_size': 10, 'align': 'center', 'bold': False})
            sheet = workbook.add_worksheet(obj.location_id.name)
            sheet.set_column(0, 12, 12)
            sheet.set_column(13, 13, 18)
            # sheet.set_column(3, 8, 25)
            # sheet.set_row(0, 25)
            # sheet.set_row(1, 25)
            # sheet.set_row(2, 25)
            sheet.merge_range('A1:C4', '')
            sheet.insert_image('A1:C4', 'myimage.png', {'image_data': image_data})
            sheet.merge_range('D1:M1', obj.company_id.name, format2)
            sheet.merge_range('D2:M2', obj.company_id.street, format2)
            sheet.merge_range('D3:M3', 'THẺ KHO', format2)
            # sheet.merge_range('D4:M4', 'TỪ NGÀY………... ĐẾN NGÀY…………...', format2)
            sheet.merge_range('D4:G4', 'TỪ NGÀY', format5)
            sheet.write('I4', 'ĐẾN NGÀY', format6)
            sheet.write('H4', obj.from_date, format7)
            sheet.write('J4', obj.to_date, format7)
            sheet.merge_range('N1:N3', 'Mã hiệu:', format_tittle)
            sheet.merge_range('B5:G5', obj.location_id.name, format6)
            sheet.merge_range('B6:G6', obj.product_id.default_code, format6)
            sheet.write('A5', 'Mã kho:', format6)
            sheet.write('A6', 'Mã hàng:', format6)

            sheet.write('F8', 'Ngày chứng từ:', format2)
            sheet.write('G8', 'Số chứng từ:', format2)
            sheet.write('H8', 'Loại chứng từ:', format2)

            sheet.write('J8', 'Tồn đầu kỳ', format2)
            sheet.write('K8', 'Nhập:', format2)
            sheet.write('L8', 'Xuất', format2)
            sheet.write('M8', 'Tồn cuối kỳ:', format2)

            sheet.merge_range('A7:A8', 'STT', format2)
            sheet.merge_range('B7:B8', 'Kho/Cửa hàng', format2)
            sheet.merge_range('C7:C8', 'Mã hàng', format2)
            sheet.merge_range('D7:D8', 'Tên hàng', format2)
            sheet.merge_range('E7:E8', 'Đơn vị tính', format2)
            sheet.merge_range('I7:I8', 'Tên đối tượng', format2)
            sheet.merge_range('J7:M7', 'Số lượng', format2)
            sheet.merge_range('F7:H7', 'Chứng từ', format2)
            sheet.merge_range('N7:N8', 'User thực hiện', format2)
            stt = 1
            row_count = 9
            qty_in = 0
            qty_out = 0
            row_num_qty = 8
            for stock_card_line in obj.move_lines:
                # qty_in = qty_in + stock_card_line.qty_in
                # qty_out = qty_out + stock_card_line.qty_out
                qty_in = stock_card_line.qty_in
                qty_out = stock_card_line.qty_out
                row_num_qty += 1
                sheet.write('J' + str(row_count), obj.opening_stock, format2)
                sheet.write('F' + str(row_count), stock_card_line.date, format7)
                sheet.write('G' + str(row_count), stock_card_line.reference, format2)
                sheet.write('K' + str(row_count), qty_in, format2)
                sheet.write('L' + str(row_count), qty_out, format2)
                sheet.write('M' + str(row_count), stock_card_line.qty_inventory, format2)
                sheet.write('N' + str(row_count), stock_card_line.user or "", format2)
                sheet.write('A' + str(row_count), stt, format2)
                sheet.write('B' + str(row_count), obj.location_id.name, format2)
                sheet.write('C' + str(row_count), obj.product_id.default_code, format2)
                sheet.write('D' + str(row_count), obj.product_id.name, format2)
                sheet.write('E' + str(row_count), obj.product_uom.name, format2)
                if stock_card_line.x_description:
                    if stock_card_line.x_description == 'NHAP':
                        sheet.write('H' + str(row_count), 'Nhập kiểm kê', format2)
                    elif stock_card_line.x_description == 'XUAT':
                        sheet.write('H' + str(row_count), 'Xuất kiểm kê', format2)
                    else:
                        sheet.write('H' + str(row_count), stock_card_line.x_description, format2)
                else:
                    product_process = self.env['product.process'].search([('name', '=', stock_card_line.move_id.origin)])
                    if product_process:
                        sheet.write('H' + str(row_count), 'Chế biến', format2)
                    else:
                        sheet.write('H' + str(row_count), 'Bán hàng', format2)
                sheet.write('I' + str(row_count), stock_card_line.partner_name or "", format2)
                stt += 1
                row_count += 1
            # sheet.write('A' + str(row_count), stt, format2)
            # sheet.write('B' + str(row_count), obj.location_id.name, format2)
            # sheet.write('C' + str(row_count), obj.product_id.default_code, format2)
            # sheet.write('D' + str(row_count), obj.product_id.name, format2)
            # sheet.write('E' + str(row_count), obj.product_uom.name, format2)

            border_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'font_size': 10
            })
            sheet.merge_range('L' + str(row_num_qty + 1) + ':' + 'N' + str(row_num_qty + 1),
                              'Hà Nội, ngày……..tháng…….năm………..',
                              format2)
            sheet.merge_range('L' + str(row_num_qty + 2) + ':' + 'N' + str(row_num_qty + 2), 'Lập phiếu',
                              format2)
            sheet.conditional_format(0, 0, row_num_qty - 1, 13,
                                     {'type': 'no_blanks', 'format': border_format})
            sheet.conditional_format(0, 0, row_num_qty - 1, 13,
                                     {'type': 'blanks', 'format': border_format})
            sheet.merge_range('L' + str(row_num_qty + 3) + ':' + 'N' + str(row_num_qty + 6), '')

            # sheet.merge_range("L11:N11",
            #                   'Hà Nội, ngày……..tháng…….năm………..',
            #                   format2)
            # sheet.merge_range("L12:N12", 'Lập phiếu',
            #                   format2)
            # sheet.conditional_format(0, 0, 9, 13,
            #                          {'type': 'no_blanks', 'format': border_format})
            # sheet.conditional_format(0, 0, 9, 13,
            #                          {'type': 'blanks', 'format': border_format})
