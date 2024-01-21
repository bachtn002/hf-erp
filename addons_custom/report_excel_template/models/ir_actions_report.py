# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api,_
from odoo.exceptions import UserError


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    export_excel = fields.Boolean('Export Excel')
    report_excel_template_id = fields.Many2one('report.excel.template','Excel Template')

    @api.model
    def render_excel_template(self, docids, data):
        if len(docids) != 1:
            raise UserError(_('Only one id is allowed for'))
        excel_template = self.report_excel_template_id
        if not excel_template or len(excel_template) != 1:
            raise UserError(_("Template %s on model %s is not unique!" % (self.report_name, self.model)))
        Export = self.env['xlsx.export']
        return Export.export_xlsx(excel_template, self.model, docids[0])