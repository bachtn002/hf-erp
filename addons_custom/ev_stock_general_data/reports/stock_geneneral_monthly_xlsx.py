from odoo import models
from odoo.exceptions import UserError, ValidationError


class StockGeneralMonthly(models.AbstractModel):
    _name = 'report.ev_stock_general_data.stock_sync_monthly_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        try:
            for obj in lines:
                format1 = workbook.add_format({'font_size': 18, 'align': 'center', 'bold': True})
                format2 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': False})
                format3 = workbook.add_format({'font_size': 12, 'align': 'right', 'bold': False})
                format4 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
                number = workbook.add_format({'num_format': '#,###.###', 'align': 'right', 'border': True})
                sheet = workbook.add_worksheet(obj.name)
                sheet.set_column(0, 0, 10)
                sheet.set_column(1, 1, 33)
                sheet.set_column(2, 2, 20)
                sheet.set_column(3, 3, 33)
                sheet.set_column(4, 4, 20)
                sheet.set_column(5, 9, 15)

                sheet.write('A1', 'STT', format1)
                sheet.write('B1', 'Địa điểm', format1)
                sheet.write('C1', 'Mã sản phẩm', format1)
                sheet.write('D1', 'Sản phẩm', format1)
                sheet.write('E1', 'Đơn vị tính', format1)
                sheet.write('F1', 'Tháng', format1)
                sheet.write('G1', 'Năm', format1)
                sheet.write('H1', 'Tồn đầu kỳ', format1)
                sheet.write('I1', 'SL Nhập', format1)
                sheet.write('J1', 'SL Xuất', format1)
                sheet.write('K1', 'Tồn Cuối', format1)

                stt = 2
                qty_begin = 0
                qty_in = 0
                qty_out = 0
                qty_end = 0
                for line in obj.line_ids:
                    sheet.write('A' + str(stt), stt, format2)
                    sheet.write('B' + str(stt), line.location_id.name, format2)
                    sheet.write('C' + str(stt), line.product_id.default_code, format2)
                    sheet.write('D' + str(stt), line.product_id.product_tmpl_id.name, format2)
                    sheet.write('E' + str(stt), line.uom_id.name, format2)
                    sheet.write('F' + str(stt), line.month, format3)
                    sheet.write('G' + str(stt), line.year, format3)
                    sheet.write('H' + str(stt), line.qty_begin if line.qty_begin != 0 else 0, number)
                    sheet.write('I' + str(stt), line.qty_in if line.qty_in != 0 else 0, number)
                    sheet.write('J' + str(stt), line.qty_out if line.qty_out != 0 else 0, number)
                    sheet.write('K' + str(stt), line.qty_end if line.qty_end != 0 else 0, number)
                    stt += 1
                    qty_begin += line.qty_begin
                    qty_in += line.qty_in
                    qty_out += line.qty_out
                    qty_end += line.qty_end

                border_format = workbook.add_format({
                    'border': 1,
                    'align': 'left',
                    'font_size': 10
                })

                sheet.write('G' + str(stt + 1), 'Tổng:', format4)
                sheet.write('H' + str(stt + 1), qty_begin, number)
                sheet.write('I' + str(stt + 1), qty_in, number)
                sheet.write('J' + str(stt + 1), qty_out, number)
                sheet.write('K' + str(stt + 1), qty_end, number)
                sheet.conditional_format(0, 0, stt, 9, {'type': 'no_blanks', 'format': border_format})
                sheet.conditional_format(0, 0, stt, 9, {'type': 'blanks', 'format': border_format})

        except Exception as e:
            raise ValidationError(e)
