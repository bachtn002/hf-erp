# -*- coding: utf-8 -*-
from odoo import fields, models, _


class StockTransferReport(models.TransientModel):
    _name = 'stock.transfer.report'
    _inherit = 'report.base'
    _auto = True
    _description = _("Stock Transfer Report")

    from_date = fields.Date(string='From date', required=True)
    to_date = fields.Date(string='To date', required=True)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse')

    _sql_constraints = [
        ('date_check', "CHECK(from_date<=to_date)",
         "The start date must be earlier than the end date!")
    ]

    def _get_default_template_view_external_id(self):
        return 'ev_report_custom_v1.stock_transfer_report_template'

    def get_download_file_name(self):
        return _('stock_transfer_report.xlsx')

    def _get_report_json(self):
        params = self.copy_data()[0]
        data = self.env['stock.transfer.store']._get_data_query(params)
        return data

    def _columns_name(self):
        return {
            '.no': 'STT',
            'name_st': 'Mã phiếu',
            'warehouse_id': 'Kho nguồn',
            'warehouse_dest_id': 'Kho đích',
            'default_code': 'Mã hàng',
            'product_name': 'Tên SP',
            'uom': 'Đơn vị tính',
            'out_quantity': 'Số lượng',
            'out_date': 'Thời gian thực hiện',
            'name_partner': 'Người tạo',
        }

    def _header_merge(self):
        return [
            ['0:0', '0:0', '.no'],
        ]

    def action_report(self):
        return super(StockTransferReport, self.with_context(renew=True)).action_report()
