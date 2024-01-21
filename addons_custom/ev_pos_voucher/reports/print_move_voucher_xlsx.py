# -*- coding: utf-8 -*-
import base64
import datetime
import io

from odoo import models
from PIL import Image


class MoveVoucherXLS(models.AbstractModel):
    _name = 'report.ev_pos_voucher.move_voucher_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        for obj in lines:
            format1 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
            format2 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': False})
            format3 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False})
            border_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'font_size': 10
            })

            sheet = workbook.add_worksheet(obj.name)
            sheet.set_column(0, 6, 25)
            sheet.set_column(4, 4, 15)
            sheet.set_column(7, 7, 20)
            sheet.set_column(8, 9, 20)

            sheet.write('A1', 'Tài khoản', format1)
            sheet.write('B1', 'Đối tác', format1)
            sheet.write('C1', 'Nhãn', format1)
            sheet.write('D1', 'Sản phẩm', format1)
            sheet.write('E1', 'Số lượng', format1)
            sheet.write('F1', 'Tài khoản phân tích', format1)
            sheet.write('G1', 'Khoản mục phí', format1)
            sheet.write('H1', 'Tiền', format1)
            sheet.write('I1', 'Nợ', format1)
            sheet.write('J1', 'Có', format1)

            index = 1
            for record in obj.line_ids:
                for line in record.account_move_id.line_ids:
                    account_name =  line.account_id.code + ' - ' + line.account_id.name
                    analytic_account_name = '[' + line.analytic_account_id.code + '] ' + line.analytic_account_id.name
                    sheet.write(index, 0, account_name, format2)
                    sheet.write(index, 1, line.partner_id.name if line.partner_id else '', format2)
                    sheet.write(index, 2, line.name, format2)
                    sheet.write(index, 3, line.product_id.name if line.product_id else '', format2)
                    sheet.write(index, 4, line.quantity, format3)
                    sheet.write(index, 5, analytic_account_name, format2)
                    sheet.write(index, 6, line.x_account_expense_item_id.name if line.x_account_expense_item_id else '', format2)
                    sheet.write(index, 7, line.currency_id.name, format2)
                    sheet.write(index, 8, '{:,.0f}'.format(line.debit).replace(',', '.'), format3)
                    sheet.write(index, 9, '{:,.0f}'.format(line.credit).replace(',', '.'), format3)
                    index += 1

            sheet.conditional_format(0, 0, index - 1, 9, {'type': 'no_blanks', 'format': border_format})
            sheet.conditional_format(0, 0, index - 1, 9, {'type': 'blanks', 'format': border_format})
