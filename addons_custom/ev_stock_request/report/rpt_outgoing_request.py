# -*- coding: utf-8 -*-
__author__ = "HoiHD on 15/01/2020"

import logging
from odoo import models, api
_logger = logging.getLogger(__name__)


class ReportExportRequest(models.Model):
    _inherit = 'stock.request'

    def action_print_export_request_report(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_request.outgoing_request_report_id/%s' % (self.id),
            'target': 'new',
            'res_id': self.id
        }
