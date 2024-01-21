# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HelpdeskTicketType(models.Model):
    _inherit = 'helpdesk.ticket.type'

    x_helpdesk_department_id = fields.Many2many('helpdesk.department', 'helpdesk_type_department_rel',
                                                'helpdesk_type_id', 'department_id',
                                                string="Helpdesk department")
    active = fields.Boolean('Active', default=True)