from odoo import models, fields, api, _


class HelpdeskDepartment(models.Model):
    _name = 'helpdesk.department'
    _description = "Helpdesk department"

    name = fields.Char('Department name', required=1)
    user_ids = fields.One2many('res.users', 'x_helpdesk_department_id', string='Department users')

    # Email xử lý ticket
    emails = fields.Text('Emails Ticket manage', help="Email list send when ticket created! Each email separate with comma!")
    helpdesk_team_id = fields.Many2one('helpdesk.team', "Helpdesk team related", required=1)


class Users(models.Model):
    _inherit = 'res.users'

    x_helpdesk_department_id = fields.Many2one('helpdesk.department', string='Helpdesk Department')
