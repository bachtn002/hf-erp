import base64
import io
from builtins import print

from PIL.Image import Image
from PIL import Image
from xlrd3.timemachine import xrange

from odoo import models


class PromotionCodeStatusReport(models.AbstractModel):
    _name = 'report.promotion.code.status.report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        for obj in lines:
            format1 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
            format2 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': False})
            format7 = workbook.add_format(
                {'num_format': 'DD-MM-YYYY', 'font_size': 10, 'align': 'center', 'bold': False})
            sheet = workbook.add_worksheet('Promotion Code')
            sheet.set_column(0, 2, 15)
            sheet.write('A1', 'Mã', format1)
            sheet.write('B1', 'Đơn hàng', format1)
            sheet.write('C1', 'Ngày sử dụng', format1)
            # print('obj', obj.promotion_voucher_status)
            row_num = 2
            # for promotion_line in obj.promotion_voucher_status:
            for promotion_line in obj.promotion_voucher_count:
                # sheet.write('A' + str(row_num), promotion_line.promotion_code, format2)
                # sheet.write('B' + str(row_num), promotion_line.pos_order, format2)
                # sheet.write('C' + str(row_num), promotion_line.date, format7)
                sheet.write('A' + str(row_num), promotion_line.promotion_code, format2)
                sheet.write('B' + str(row_num), promotion_line.pos_order_uid, format2)
                sheet.write('C' + str(row_num), promotion_line.date, format7)
                row_num += 1
