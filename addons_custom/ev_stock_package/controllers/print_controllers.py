# -*- coding: utf-8 -*-
from odoo import _, SUPERUSER_ID
from odoo.http import Controller, route, request
import json
import base64

class ReportControllerInherit(Controller):

    # ------------------------------------------------------
    # Report controllers
    # ------------------------------------------------------
    @route([
        '/report/pdf_custom/<reportname>/<docids>',
    ], type='json', auth='user', website=True)
    def report_pdf_routes(self,reportname ,docids=None, **data):
        report = request.env['ir.actions.report']._get_report_from_name(reportname)
        context = dict(request.env.context)
        if data.get('options'):
            data.update(json.loads(data.pop('options')))
        if docids:
            docids = [int(i) for i in docids.split(',')]
        if data.get('context'):
            data['context'] = json.loads(data['context'])
            if data['context'].get('lang'):
                del data['context']['lang']
            context.update(data['context'])
        pdf = report.with_context(context)._render_qweb_pdf(docids, data=data)[0]
        pdf_base64 = base64.b64encode(pdf)
        return pdf_base64