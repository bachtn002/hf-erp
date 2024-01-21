from odoo import models, fields, api, _


class HelpdeskEmail(models.Model):
    _name = 'helpdesk.email'
    _description = 'Email to receive notification ticket'

    name = fields.Char('Email', required=True)
    helpdesk_department_id = fields.Many2one('helpdesk.department', 'Department', required=True)
