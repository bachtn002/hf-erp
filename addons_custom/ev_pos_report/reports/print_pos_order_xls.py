# -*- coding: utf-8 -*-
import base64
import datetime
import io

from odoo import models
from dateutil.relativedelta import relativedelta


class PosOderXLS(models.AbstractModel):
    _name = 'report.ev_pos_report.pos_order_xlsx'
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

            sheet = workbook.add_worksheet(obj.name)
            sheet.set_column(1, 14, 19)

            sheet.write('A1', 'Đơn hàng', format2)
            sheet.write('B1', 'Ngày mua hàng', format2)
            sheet.write('C1', 'Khách hàng', format2)
            sheet.write('D1', 'SĐT', format2)
            sheet.write('E1', 'Tổng tiền', format2)
            sheet.write('F1', 'Cửa hàng', format2)
            sheet.write('G1', 'Nhân viên', format2)
            sheet.write('H1', 'Ghi chú', format2)
            # sheet.write('I1', 'Phương thức thanh toán', format2)
            # sheet.write('I1', 'Số tiền', format2)

            stt = 1
            x = 2
            amount_total = 0
            id_temp = ""
            for record in obj.order_lines:
                if record.order_id.name == id_temp:
                    x -= 1
                else:
                    id_temp = record.order_id.name
                sheet.write('A' + str(x), record.order_id.name or "", format4)
                sheet.write('B' + str(x), record.date + relativedelta(hours=7) or "", format7)
                sheet.write('C' + str(x), record.customer_id.name or "", format4)
                sheet.write('D' + str(x), record.customer_id.phone or "", format4)
                sheet.write('E' + str(x), record.amount_total, money)
                sheet.write('F' + str(x), obj.pos_shop_id.name or "", format4)
                sheet.write('G' + str(x), record.user_id.name or "", format4)
                sheet.write('H' + str(x), record.note or "", format4)
                # sheet.write('I' + str(x), record.payment_method_id.name, format4)
                # sheet.write('I' + str(x), "{:,.0f}".format(record.amount_payment), money)
                x += 1

            # sheet.conditional_format(0, 0, x, 14, {'type': 'no_blanks', 'format': border_format})
