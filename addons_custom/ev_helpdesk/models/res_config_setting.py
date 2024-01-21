from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    days_allow_back_to_new_ticket = fields.Integer(string="Days", default=3)
    stage_allow_user_back_ticket = fields.Many2one('helpdesk.stage', string="Stage", required=1)
    link_drive = fields.Text(string="Link drive", help="Link document guide user using system!")

    _sql_constraints = [
        ('days_ticket_greater_zero', 'check(days_allow_back_to_new_ticket > 0)', 'Days must be greater than zero'),
    ]

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        stage = self.env['ir.config_parameter'].sudo().get_param('ev_helpdesk.stage_allow_user_back_ticket')
        stage_id = self.env['helpdesk.stage'].browse(int(stage))
        res.update(
            days_allow_back_to_new_ticket=self.env['ir.config_parameter'].sudo().get_param(
                'ev_helpdesk.days_allow_back_to_new_ticket'),
            stage_allow_user_back_ticket=stage_id,
            link_drive=self.env['ir.config_parameter'].sudo().get_param(
                'ev_helpdesk.link_drive'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()

        helpdesk_days_allow = self.days_allow_back_to_new_ticket and self.days_allow_back_to_new_ticket or False
        stage_allow = self.stage_allow_user_back_ticket and self.stage_allow_user_back_ticket.id or False
        link_drive = self.link_drive and self.link_drive or False

        param.set_param('ev_helpdesk.days_allow_back_to_new_ticket', helpdesk_days_allow)
        param.set_param('ev_helpdesk.stage_allow_user_back_ticket', stage_allow)
        param.set_param('ev_helpdesk.link_drive', link_drive)
