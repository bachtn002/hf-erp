# -*- coding: utf-8 -*-
from odoo import api, models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    x_helpdesk_department_ids = fields.Many2many('helpdesk.department', 'users_helpdesk_department_rel', 'user_id',
                                                 'helpdesk_department_id', string="Helpdesk departments")

    x_is_allow_helpdesk_department = fields.Boolean('Is allow helpdesk department')
