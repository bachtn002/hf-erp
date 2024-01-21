# -*- coding: utf-8 -*-
from odoo import models, fields, _


class ReportStyleLine(models.Model):
    _name = 'report.style.line'
    _description = 'Report Style Line'

    style_id = fields.Many2one('report.style', string='Style')
    css_key = fields.Char(string='Key')
    css_value = fields.Char(string='Value')
    type = fields.Selection([('thead', 'thead'), ('tbody', 'tbody'),
                             ('tfoot', 'tfoot'), ('index', 'Index')],
                            default='thead',
                            string='Type')
