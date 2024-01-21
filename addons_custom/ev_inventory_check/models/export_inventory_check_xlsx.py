from odoo import models
from datetime import datetime, timedelta
from xlsxwriter.utility import xl_rowcol_to_cell
import base64
import io
from PIL.Image import Image
from PIL import Image


class ExportStockInventory(models.AbstractModel):
    _name = 'report.ev_inventory_check.export_stock_inventory'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        for obj in lines:
            # One sheet by partner
            format1 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
            format2 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': False})
            format_tittle = workbook.add_format({'font_size': 10, 'align': 'top', 'bold': False})
            format6 = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': False})
            format5 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False})
            format4 = workbook.add_format({'font_size': 10, 'bold': False})
            format3 = workbook.add_format({'font_size': 18, 'align': 'center', 'bold': False})
            format7 = workbook.add_format(
                {'num_format': 'mmm d yyyy hh:mm AM/PM', 'font_size': 10, 'align': 'left', 'bold': False})
            money = workbook.add_format({'num_format': '#,##0', 'align': 'left', 'border': True})
            sheet = workbook.add_worksheet(obj.name)
            sheet.set_column(1, 3, 20)

            sheet.write('A1', 'STT', format2)
            sheet.write('B1', 'Mã hàng:', format2)
            sheet.write('C1', 'Tên hàng', format2)
            sheet.write('D1', 'Nhóm Hàng', format2)
            sheet.write('E1', 'Đơn vị tính', format2)
            sheet.write('F1', 'Kho', format2)
            sheet.write('G1', 'Số lượng lý thuyết', format2)
            sheet.write('H1', 'Số lượng thực tế', format2)
            sheet.write('I1', 'Chênh lệch', format2)
            sheet.write('J1', 'Giá vốn', format2)
            sheet.write('K1', 'Giá bán', format2)
            sheet.write('L1', 'Giá trị chênh lệch', format2)

            index = 2
            for line in obj.line_ids:
                standard_price = line.product_id.standard_price
                price_unit = line.product_id.list_price
                sheet.write('A' + str(index), index - 1, format6)
                sheet.write('B' + str(index), line.product_id.default_code, format6)
                sheet.write('C' + str(index), line.product_id.name, format6)
                sheet.write('D' + str(index), line.product_id.categ_id.name, format6)
                sheet.write('E' + str(index), line.product_id.uom_id.name, format6)
                sheet.write('F' + str(index), line.location_id.name, format6)
                sheet.write('G' + str(index), line.theoretical_qty, format5)
                sheet.write('H' + str(index), line.product_qty, format5)
                sheet.write('I' + str(index), line.difference_qty, format5)
                sheet.write('J' + str(index), standard_price, money)
                sheet.write('K' + str(index), price_unit, money)
                sheet.write('L' + str(index), abs(line.difference_qty * standard_price) if line.difference_qty > 0
                                                                else abs(line.difference_qty * price_unit), money)

                index += 1

            border_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'font_size': 10
            })
            # sheet.merge_range('D' + str(index + 2) + ':' + 'F' + str(index + 2),
            #                   'Hà Nội, ngày……..tháng…….năm………..',
            #                   format2)
            # sheet.merge_range('D' + str(index + 3) + ':' + 'F' + str(index + 3), 'Lập phiếu',
            #                   format2)
            sheet.conditional_format(0, 0, index - 2, 11,
                                     {'type': 'no_blanks', 'format': border_format})
            sheet.conditional_format(0, 0, index - 2, 11,
                                     {'type': 'blanks', 'format': border_format})
