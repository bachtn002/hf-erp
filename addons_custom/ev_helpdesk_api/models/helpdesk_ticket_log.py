# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HelpdeskTicketLog(models.Model):
    _name = 'helpdesk.ticket.log'
    _description = "Helpdesk ticket log"

    data = fields.Text(string="Data")
    message = fields.Char(string="Message")
