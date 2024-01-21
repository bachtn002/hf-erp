# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm


class FileStore(models.TransientModel):
    _name = 'report.file'

    '''
        - Nơi lưu trữ file.
    '''

    name = fields.Char('File name')
    code = fields.Char('Code')
    value = fields.Binary('File Value')

    def _download_file(self, name, code):
        ReportFile = self.env['report.file']
        if code:
            report_id = ReportFile.search([('code', '=', code)], limit=1)
            if report_id.id == False:
                raise except_orm('Cảnh báo!', 'Không tìm thấy file với khóa bạn chọn!')
        else:
            raise except_orm('Cảnh báo!', 'Vui lòng thêm khóa để tìm kiếm!')

        return {
            'name': name,
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=report.file&id=%s&filename_field=name&field=value&download=true&filename=%s" %(report_id.id, name),
            'target': 'current',
        }

