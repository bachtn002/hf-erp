# -*- coding: utf-8 -*-
import base64
import datetime
import io

from odoo import models
from PIL import Image


class StockCardXLS(models.AbstractModel):
    _name = 'report.ev_account_statement.account_statement_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        format1 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})

        sheet = workbook.add_worksheet('Mẫu')
        sheet.set_column(4, 4, 4)

        sheet.write('A1', 'Mã giao địch', format1)
        sheet.write('B1', 'Ngày hiệu lực', format1)
        sheet.write('C1', 'Số chứng từ', format1)
        sheet.write('D1', 'Nội dung nộp tiền (MACUAHANG/NOIDUNG)', format1)
        sheet.write('E1', 'Số tiền', format1)
