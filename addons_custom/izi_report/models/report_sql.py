# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Report(models.TransientModel):
    _name = 'report.sql'

    '''
        - Đưa thủ tục và chạy trên web!
    '''
    name = fields.Char(string='Name', default='Record')
    sql = fields.Text('SQL')

    def run_sql(self):
        self.env.cr.execute(self.sql)
        return