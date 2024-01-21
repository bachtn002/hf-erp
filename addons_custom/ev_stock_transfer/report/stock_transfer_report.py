# -*- coding: utf-8 -*-

from odoo import models


class StockTransferXLS(models.AbstractModel):
    _name = 'report.ev_stock_transfer.stock_transfer_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        for obj in lines:
            format_tittle = workbook.add_format({'font_size': 10, 'align': 'top', 'bold': False})
            format1 = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': True})
            format2 = workbook.add_format({'font_size': 12, 'align': 'right', 'bold': False})
            format3 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': False})
            format4 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': False})
            format7 = workbook.add_format(
                {'num_format': 'dd-MM-yyyy HH:mm', 'font_size': 12, 'align': 'center', 'bold': True})
            border_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'font_size': 10
            })

            sheet = workbook.add_worksheet(obj.name)
            sheet.set_column(1, 8, 25)
            sheet.write('A1', 'STT', format1)
            sheet.write('B1', 'Mã SP', format1)
            sheet.write('C1', 'Tên SP', format1)
            sheet.write('D1', 'Đơn vị', format1)
            sheet.write('E1', 'Số lượng', format1)
            sheet.write('F1', 'Giá bán', format1)
            sheet.write('G1', 'Ghi chú', format1)

            index = 1
            for line in obj.transfer_line_ids:
                if line:
                    sheet.write(index, 0, index, format2)
                    sheet.write(index, 1, line.product_id.default_code, format3)
                    sheet.write(index, 2, line.product_id.name, format3)
                    sheet.write(index, 3, line.product_uom.name, format3)
                    sheet.write(index, 4, line.quantity, format2)
                    sheet.write(index, 5, line.product_id.lst_price, format2)
                    sheet.write(index, 6, line.note if line.note != False else '', format3)
                    index += 1

            sheet.conditional_format(0, 0, index-1, 6, {'type': 'no_blanks', 'format': border_format})
            sheet.conditional_format(0, 0, index-1, 6, {'type': 'blanks', 'format': border_format})
