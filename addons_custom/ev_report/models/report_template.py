# -*- coding: utf-8 -*-
from odoo import models, fields


class ReportTemplate(models.Model):
    _name = 'report.template'
    _description = 'Report Template'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')
    header_html = fields.Html(string='Header Html')
    footer_html = fields.Html(string='Footer Html')
    style_id = fields.Many2one('report.style', string='Style')
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=lambda self: self.env.company.id)
    active = fields.Boolean(string='Active', default=False)

    _sql_constrains = [
        ('unique_code', 'unique(code)', 'Code must be unique')
    ]
