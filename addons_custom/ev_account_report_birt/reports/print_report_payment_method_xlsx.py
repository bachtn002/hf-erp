import base64
import datetime
import io


from odoo import models
from PIL import Image


class PosOderPaymentMethodXLS(models.AbstractModel):
    _name = 'report.ev_account_report_birt.pos_payment_method_xlsx'
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
            sheet.set_column(0, 1, 30)
            sheet.set_column(2, 5, 20)

            sheet.write('A1', 'Phương thức thanh toán', format2)
            sheet.write('B1', 'Đối tượng cửa hàng', format2)
            sheet.write('C1', 'Số dư đầu', format2)
            sheet.write('D1', 'Phát sinh nợ', format2)
            sheet.write('E1', 'Phát sinh có', format2)
            sheet.write('F1', 'Số dư', format2)

            x = 2
            for record in obj.report_pos_payment_method_line_ids:
                sheet.write('A' + str(x), record.pos_payment_method_id.name or "", format4)
                sheet.write('B' + str(x), record.account_analytic_id.name or "", format7)
                sheet.write('C' + str(x), record.intital_balance if record.intital_balance else '0', money)
                sheet.write('D' + str(x), record.debit if record.debit else '0', money)
                sheet.write('E' + str(x), record.credit if record.credit else '0', money)
                sheet.write('F' + str(x), record.balance if record.balance else '0', money)
                x += 1

            sheet.conditional_format(0, 0, x-2, 5, {'type': 'no_blanks', 'format': border_format})
            sheet.conditional_format(0, 0, x-2, 5, {'type': 'blanks', 'format': border_format})