import base64
import io
from builtins import print

from PIL.Image import Image
from PIL import Image
from xlrd3.timemachine import xrange

from odoo import models


class PromotionCodeReport(models.AbstractModel):
    _name = 'report.promotion.code.report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        for obj in lines:
            format1 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
            format2 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': False})
            format7 = workbook.add_format(
                {'num_format': 'DD-MM-YYYY', 'font_size': 10, 'align': 'center', 'bold': False})
            sheet = workbook.add_worksheet('Promotion Code')
            sheet.set_column(0, 2, 15)
            sheet.write('A1', 'Mã:', format1)
            sheet.write('B1', 'Ngày phát hành', format1)
            sheet.write('C1', 'Ngày hết hạn', format1)
            print('obj', obj.promotion_voucher_line)
            row_num = 2
            for promotion_line in obj.promotion_voucher_line:
                sheet.write('A' + str(row_num), promotion_line.name, format2)
                sheet.write('B' + str(row_num), obj.date, format7)
                sheet.write('C' + str(row_num), obj.expired_date, format7)
                row_num += 1
