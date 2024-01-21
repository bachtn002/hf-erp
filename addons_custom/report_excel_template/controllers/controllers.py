# -*- coding: utf-8 -*-
import json
import io
from odoo import http
from odoo.http import route
from odoo.addons.web.controllers import main as report
from odoo.tools.safe_eval import safe_eval
import time
from werkzeug.urls import url_decode
from odoo.http import content_disposition, request, \
    serialize_exception as _serialize_exception
from odoo.tools import html_escape

class ReportViewController(report.ReportController):

    @route(["/report_excel_template"], type='http', auth='user')
    def export_excel(self, **kw):
        report, report_name = request.env['report.excel.template']._get_template_export_excel(**kw)
        filename = "%s.%s" % (report_name, 'xlsx')
        response = request.make_response(report.read(),
                                         headers=[('Content-Type',
                                                   'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                                                  ('Content-Disposition',content_disposition(filename))
                                                  ],)
        report.close()
        return response

    @route([
        '/report/<converter>/<reportname>',
        '/report/<converter>/<reportname>/<docids>',
    ], type='http', auth='user', website=True)
    def report_routes(self, reportname, docids=None, converter=None, **data):
        report = request.env['ir.actions.report']._get_report_from_name(reportname)
        context = dict(request.env.context)
        if report.export_excel:
            if docids:
                docids = [int(i) for i in docids.split(',')]
            if data.get('options'):
                data.update(json.loads(data.pop('options')))
            if data.get('context'):
                data['context'] = json.loads(data['context'])
                if data['context'].get('lang'):
                    del data['context']['lang']
                context.update(data['context'])
            report = report.with_context(context).render_excel_template(
                docids, data=data
            )
            docxhttpheaders = [('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')]
            response = request.make_response(report, headers=docxhttpheaders)
            return response
        else:
            return super(ReportViewController, self).report_routes(reportname,docids,converter,**data)

    @route(['/report/download'], type='http', auth="user")
    def report_download(self, data, token):
        requestcontent = json.loads(data)
        url, type = requestcontent[0], requestcontent[1]
        try:
            if type in ['qweb-pdf', 'qweb-text']:
                converter = 'pdf' if type == 'qweb-pdf' else 'text'
                extension = 'pdf' if type == 'qweb-pdf' else 'txt'

                pattern = '/report/pdf/' if type == 'qweb-pdf' else '/report/text/'
                reportname = url.split(pattern)[1].split('?')[0]

                docids = None
                if '/' in reportname:
                    reportname, docids = reportname.split('/')

                if docids:
                    # Generic report:
                    response = self.report_routes(reportname, docids=docids, converter=converter)
                else:
                    # Particular report:
                    data = url_decode(url.split('?')[1]).items()  # decoding the args represented in JSON
                    response = self.report_routes(reportname, converter=converter, **dict(data))

                report = request.env['ir.actions.report']._get_report_from_name(reportname)

                if not report.export_excel:
                    return super(ReportViewController, self).report_download(data, token)
                extension = 'xlsx'
                filename = "%s.%s" % (report.name, extension)
                if docids:
                    ids = [int(x) for x in docids.split(",")]
                    obj = request.env[report.model].browse(ids)
                    if report.print_report_name and not len(obj) > 1:
                        report_name = safe_eval(report.print_report_name, {'object': obj, 'time': time})
                        filename = "%s.%s" % (report_name, extension)
                response.headers.add('Content-Disposition', content_disposition(filename))
                response.set_cookie('fileToken', token)
                return response
            else:
                return
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': "Odoo Server Error",
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))