from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from ...izi_report.models import excel_style
from io import BytesIO
import xlsxwriter
import base64


class ProductRelease(models.Model):
    _inherit = 'product.release'

    apply_promotion = fields.Boolean('Apply together with promotion', track_visibility='onchange')
    limit_config = fields.Boolean('Limit number of Pos apply voucher', track_visibility='onchange')
    config_ids = fields.Many2many('pos.config', string='POS Apply')
    limit_voucher = fields.Boolean('Limit number of voucher apply in the order', track_visibility='onchange')
    limit_qty = fields.Integer('Quantity', default=5, track_visibility='onchange')
    @api.onchange('limit_qty')
    def onchange_limit_qty(self):
        if self.limit_qty <= 0:
            raise ValidationError(_('Limited Quantity must be greater than 0!'))

    def action_export_excel(self):
        self = self.sudo()
        file = BytesIO()
        wb = xlsxwriter.Workbook(file, {'in_memory': True})
        style_excel = excel_style.get_style(wb)
        wssheet = wb.add_worksheet('DS Mã phiếu mua hàng')
        wssheet.fit_to_pages(1, 0)
        first_row = self.add_header_report(wssheet, style_excel)
        self.write_row(wssheet, style_excel, first_row)
        namefile = u'DANH SÁCH MÃ PHIẾU MUA HÀNG.xlsx'
        wb.close()
        file.seek(0)
        out = base64.encodestring(file.getvalue())
        file.close()
        # Insert dữ liệu file vào bảng tạm
        code = 'Code_voucher'
        self._cr.execute('''DELETE FROM report_file''')
        self.env['report.file'].create({
            'code': code,
            'name': namefile,
            'value': out
        })
        self.invalidate_cache()
        return self.env['report.file']._download_file(namefile, code)

    def add_header_report(self, wssheet, style_excel):
        # table
        col = 0
        row = 0
        wssheet.write(row, col, 'Mã phiếu mua hàng', style_excel['style_12_bold_center_border'])
        wssheet.write(row, col + 1, 'Khách hàng', style_excel['style_12_bold_center_border'])
        wssheet.write(row, col + 2, 'Người sử dụng', style_excel['style_12_bold_center_border'])
        wssheet.write(row, col + 3, 'Trạng thái', style_excel['style_12_bold_center_border'])
        return row + 1

    def write_row(self, wssheet, style_excel, row):
        col = 0
        # chinh do rong
        wssheet.set_column(0, 0, width=20)
        wssheet.set_column(1, 1, width=15)
        wssheet.set_column(2, 2, width=15)
        wssheet.set_column(3, 3, width=20)
        # do du lieu
        for item in self.stock_production_lot_ids:
            state = ''
            if item.x_state == 'draft':
                state = 'Mới'
            elif item.x_state == 'activated':
                state = 'Đã kích hoạt'
            elif item.x_state == 'available':
                state = 'Có thể sử dụng'
            elif item.x_state == 'used':
                state = 'Đã sử dụng'
            elif item.x_state == 'expired':
                state = 'Hết hạn'
            elif item.x_state == 'destroy':
                state = 'Đã hủy'
            elif item.x_state == 'lock':
                state = 'Lock'
            wssheet.write(row, col, item.name, style_excel['style_12_left_data'])
            wssheet.write(row, col + 1, item.x_customer_id.name if item.x_customer_id else None,
                          style_excel['style_12_left_data'])
            wssheet.write(row, col + 2, item.x_use_customer_id.name if item.x_use_customer_id else None,
                          style_excel['style_12_left_data'])
            wssheet.write(row, col + 3, state, style_excel['style_12_left_data'])
            row += 1
