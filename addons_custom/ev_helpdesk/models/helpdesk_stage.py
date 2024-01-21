from odoo import api, fields, models


class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    x_color = fields.Char('Color', help="Color show for stage in portal. Eg: #17a2b8")
    is_cancel = fields.Boolean('Canceling Stage', help='Tickets in this stage are considered as cancel request')
    is_start = fields.Boolean('Starting Stage', help='Tickets in this stage are considered as New')

    @api.model
    def get_color_stages(self):
        stages = self.env['helpdesk.stage'].search_read([('x_color', '!=', False)], ['x_color'])
        colors = {stage['id']: stage['x_color'] for stage in stages}
        return colors
