# -*- coding: utf-8 -*-
from odoo import models, fields, _


class ReportStyle(models.Model):
    _name = 'report.style'
    _description = 'Report Style'

    name = fields.Char(string='Name', default=_('Report Style'))
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=lambda self: self.env.company.id)
    # thead
    thead_line_ids = fields.One2many('report.style.line',
                                     'style_id',
                                     string='Table Head Style',
                                     domain=[('type', '=', 'thead')],
                                     context={'default_type': 'thead'})
    # tbody
    tbody_line_ids = fields.One2many('report.style.line',
                                     'style_id',
                                     string='Table Body Style',
                                     domain=[('type', '=', 'tbody')],
                                     context={'default_type': 'tbody'})
    # tfoot
    tfoot_line_ids = fields.One2many('report.style.line',
                                     'style_id',
                                     string='Table Foot Style',
                                     domain=[('type', '=', 'tfoot')],
                                     context={'default_type': 'tfoot'})
    # index - total
    index_line_ids = fields.One2many('report.style.line',
                                     'style_id',
                                     string='Table Index/Total Style',
                                     domain=[('type', '=', 'index')],
                                     context={'default_type': 'index'})

    def get_css_thead(self):
        css = []
        for line in self.thead_line_ids:
            css.append(line.css_key + ': ' + line.css_value)
        return '; '.join(css)

    def get_css_tbody(self):
        css = []
        for line in self.tbody_line_ids:
            css.append(line.css_key + ': ' + line.css_value)
        return '; '.join(css)

    def get_css_tfoot(self):
        css = []
        for line in self.tfoot_line_ids:
            css.append(line.css_key + ': ' + line.css_value)
        return '; '.join(css)

    def get_css_index(self):
        css = []
        for line in self.index_line_ids:
            css.append(line.css_key + ': ' + line.css_value)
        return '; '.join(css)
