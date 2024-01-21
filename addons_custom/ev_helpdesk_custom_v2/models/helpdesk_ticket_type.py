from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HelpdeskTicketType(models.Model):
    _inherit = 'helpdesk.ticket.type'

    name = fields.Char('Type', required=True, translate=False)




