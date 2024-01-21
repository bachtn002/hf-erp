from odoo import fields, models, _

class RptCashStatementReport(models.TransientModel):
    _name = "rpt.cash.statement.report"
    _inherit = "report.base"
    _auto = True
    _description = "Báo Cáo kiểm Quỹ Cuối Ngày"

    to_date = fields.Date(string='Date')

    def _get_default_template_view_external_id(self):
        return 'ev_report_custom_v1.rpt_cash_statement_data'

    def get_download_file_name(self):
        return _('bao_cao_kiem_quy_cuoi_ngay.xlsx')

    def _get_report_json(self):
        params = self.copy_data()[0]
        data = self.env['rpt.cash.statement.store'].get_data(**params)
        return data

    def _columns_name(self):
        return {
            '.no': 'STT',
            'macuahang': 'Mã cửa hàng',
            'tencuahang': 'Tên cửa hàng',
            'tenvung': 'Vùng/miền',
            'start_at': 'Ngày mở phiên',
            'stop_at': 'Ngày đóng phiên',
            'doanhthutrenpm': 'Doanh thu TM ngày',
            'quycuoingay': 'Số chốt quỹ cuối ngày',
            'chenhlech': 'Số chênh lệch',
            'lydo': 'Giải trình chênh lệch',
        }

    def action_report(self):
        return super(RptCashStatementReport, self.with_context(renew=True)).action_report()
