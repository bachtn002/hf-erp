# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.addons.ev_report.wizards.report_base import _money_format
import tempfile
import base64
import pandas as pd


class StockDocumentReport(models.TransientModel):
    _name = 'stock.document.report'
    _inherit = 'report.base'
    _auto = True
    _description = _("Stock Document Report")

    from_date = fields.Date(string='From date', required=True)
    to_date = fields.Date(string='To date', required=True)
    location_ids = fields.Many2many('stock.location', string='Locations')
    product_ids = fields.Many2many('product.product', string='Products')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    x_all_internal = fields.Boolean('All Location Internal')
    state = fields.Selection([
        ('no_done', 'No Done'),
        ('done', 'Done'),
        ('all', 'All')],
        default='no_done', string="State")
    total_quantity = fields.Float(store=False)
    is_accountant = fields.Boolean()

    _sql_constraints = [
        ('date_check', "CHECK(from_date<=to_date)",
         "The start date must be earlier than the end date!")
    ]

    def _get_default_template_view_external_id(self):
        return 'ev_report_custom_v1.stock_document_report_template'

    def get_download_file_name(self):
        return _('stock_document_report.xlsx')

    def _get_report_json(self):
        params = self.copy_data()[0]
        state = self.state
        data = self.env['stock.document.store'].get_data(params, state)
        self.total_quantity = data['summary']['total_quantity']
        return data['data']

    def _columns_name(self):
        return {
            '.no': 'STT',
            'ngay': 'Ngày GD',
            'ten': 'Mã phiếu xuất/nhập',
            'mct': 'Mã chứng từ',
            'lct': 'Loại chứng từ',
            'kho_xuat': 'Kho xuất',
            'kho_nhap': 'Kho nhập',
            'marefkh': 'Mã đối tác',
            'tenkh': 'Đối tác',
            'masp': 'Mã SP',
            'product_name': 'Tên SP',
            'lot_name': 'Lot/Serial',
            'dv': 'ĐVT',
            'sl': 'SL',
            'dongia': 'Đơn giá',
            'giatri': 'Giá trị',
            'diengiai': 'Diễn giải',
            'state': 'Trạng thái',
            'note': 'Ghi chú',
        }

    def _header_merge(self):
        return [
            ['0:0', '0:0', '.no'],
        ]

    def _footer_merge(self):
        return [
            ['0:0', '12:0', 'Tổng'],
            ['13:0', '13:0', _money_format(self.total_quantity)],
        ]

    def action_report(self):
        #is_accountant : kế toán xem báo cáo
        if not self._context.get('is_accountant'):
            self.is_accountant = False
        return super(StockDocumentReport, self.with_context(renew=True)).action_report()

    def action_report_accountant(self):
        self.is_accountant = True
        return self.with_context(is_accountant=True).action_report()

    def action_export_excel(self):
        if self.is_accountant:
            return super(StockDocumentReport, self.with_context(is_accountant=True)).action_export_excel()
        return super(StockDocumentReport, self).action_export_excel()