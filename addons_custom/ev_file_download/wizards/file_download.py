# -*- coding: utf-8 -*-

from odoo import models, fields


class FileDownload(models.TransientModel):
    _name = 'file.download'
    _description = 'File Download'

    name = fields.Char('File name', required=True)
    datas = fields.Binary('File', required=True)

    def download(self, file_name, file_data):
        file_download = self.create({'name': file_name, 'datas': file_data})
        return file_download._download()

    def _prepare_download(self):
        return {
            'filename_field': 'name',
            'download': 'true',
            'filename': self.name
        }

    def _params_to_query_string(self, params):
        query_string = ''
        for key, value in params.items():
            query_string += '?' if not query_string else '&'
            query_string += f'{key}={str(value)}'
        return query_string

    def _download(self):
        params = self._prepare_download()
        url = 'web/content/file.download/{}/datas{}'.format(
            self.id, self._params_to_query_string(params))
        return {
            'name': self.name,
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'current',
        }
