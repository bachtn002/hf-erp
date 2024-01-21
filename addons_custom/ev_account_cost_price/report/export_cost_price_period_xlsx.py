
from odoo import models
from datetime import datetime, timedelta
from xlsxwriter.utility import xl_rowcol_to_cell


class ExportCostPricePeriod(models.AbstractModel):
    _name = 'report.ev_cost_price_period.export_cost_price_period'
    _inherit = 'report.odoo_report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        editable = workbook.add_format({'bold': True, 'border': 1})
        no_bold = workbook.add_format({'bold': False, 'border': 1})
        editable.set_align('center')
        editable.set_align('vcenter')
        no_bold.set_align('center')
        no_bold.set_align('vcenter')
        ws = workbook.add_worksheet("Sản phẩm")
        ws.set_column(0, 0, 10)
        ws.set_column(1, 1, 30)
        ws.set_column(2, 2, 30)
        ws.set_column(3, 3, 30)
        ws.set_column(4, 4, 30)
        ws.set_column(5, 5, 40)
        ws.set_column(6, 6, 15)
        ws.set_column(7, 7, 20)
        ws.set_column(8, 8, 20)
        ws.write(0, 0, u'STT', editable)
        ws.write(0, 1, u'Mã SP', editable)
        ws.write(0, 2, u'Sản phẩm', editable)
        ws.write(0, 3, u'ĐVT', editable)
        ws.write(0, 4, u'SL đầu kỳ', editable)
        ws.write(0, 5, u'GT đầu kỳ', editable)
        ws.write(0, 6, u"SL nhập", editable)
        ws.write(0, 7, u"GT nhập", editable)
        ws.write(0, 8, u"Giá vốn", editable)
        index = 1
        for line in lines.period_lines:
            ws.write(index, 0, index, editable)
            ws.write(index, 1, line.product_id.default_code, no_bold)
            ws.write(index, 2, line.product_id.product_tmpl_id.name, no_bold)
            ws.write(index, 3, line.product_id.product_tmpl_id.uom_id.name, no_bold)
            ws.write(index, 4, line.qty_initial, no_bold)
            ws.write(index, 5, line.value_initial, no_bold)
            ws.write(index, 6, line.qty_in, no_bold)
            ws.write(index, 7, line.value_in, no_bold)
            ws.write(index, 8, line.standard_price, no_bold)
            index += 1