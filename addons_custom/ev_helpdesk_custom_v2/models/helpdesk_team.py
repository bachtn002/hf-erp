from odoo import models, fields, api, _

class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    def action_view_ticket(self):
        action = self.env["ir.actions.server"]._for_xml_id("ev_helpdesk.action_server_ticket_department_assigned_filter")
        action['display_name'] = self.name
        return action