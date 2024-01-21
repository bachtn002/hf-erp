from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_call_ship = fields.Boolean(related='company_id.x_call_ship', string='Call Ship', readonly=False)
