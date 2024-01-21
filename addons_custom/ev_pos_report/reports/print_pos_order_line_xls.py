# -*- coding: utf-8 -*-
import base64
import datetime
import io
import locale

from odoo import models
from dateutil.relativedelta import relativedelta


class PosOrderLineXLS(models.AbstractModel):
    _name = 'report.ev_pos_report.pos_order_line_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        for obj in lines:
            format_tittle = workbook.add_format({'font_size': 10, 'align': 'top', 'bold': False})
            format1 = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': True})
            format2 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
            format3 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False})
            format4 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': False, 'border': True})
            format7 = workbook.add_format(
                {'num_format': 'dd-MM-yyyy HH:mm', 'font_size': 10, 'align': 'center', 'bold': False, 'border': True})
            border_format = workbook.add_format({
                'border': 1,
            })
            money = workbook.add_format({'num_format': '#,##0', 'align': 'right', 'border': True})

            locale.setlocale(locale.LC_ALL, '')

            sheet = workbook.add_worksheet(obj.name)
            sheet.set_column(1, 14, 19)

            sheet.write('A1', 'Đơn hàng', format2)
            sheet.write('B1', 'Ngày mua hàng', format2)
            sheet.write('C1', 'Khách hàng', format2)
            sheet.write('D1', 'SĐT', format2)
            sheet.write('E1', 'Mã sản phẩm', format2)
            sheet.write('F1', 'Sản phẩm', format2)
            sheet.write('G1', 'SL', format2)
            sheet.write('H1', 'Đơn giá', format2)
            sheet.write('I1', 'Thành tiền', format2)
            sheet.write('J1', 'Tổng chiết khấu', format2)
            sheet.write('K1', 'Thực thu', format2)
            sheet.write('L1', 'Cửa hàng', format2)
            sheet.write('M1', 'Nhân viên', format2)
            sheet.write('N1', 'Ghi chú', format2)

            stt = 1
            x = 2
            real_money = 0

            for record in obj.order_line_lines:
                real_money = record.amount_total - record.discount
                sheet.write('A' + str(x), record.order_id.name or "", format4)
                sheet.write('B' + str(x), record.order_id.date_order + relativedelta(hours=7) or "", format7)
                sheet.write('C' + str(x), record.customer_id.name or "", format4)
                sheet.write('D' + str(x), record.customer_id.phone or "", format4)
                sheet.write('E' + str(x), record.product_id.default_code or "", format4)
                sheet.write('F' + str(x), record.product_id.product_tmpl_id.name or "", format4)
                sheet.write('G' + str(x), record.quantity, money)
                sheet.write('H' + str(x), record.price_unit, money)
                sheet.write('I' + str(x), record.amount_total, money)
                sheet.write('J' + str(x), record.discount, money)
                sheet.write('K' + str(x), real_money, money)
                sheet.write('L' + str(x), obj.pos_shop_id.name or "", format4)
                sheet.write('M' + str(x), record.order_id.user_id.name or "", format4)
                sheet.write('N' + str(x), record.order_id.note or "", format4)
                x += 1

            # sheet.conditional_format(0, 0, x, 14, {'type': 'no_blanks', 'format': border_format})
