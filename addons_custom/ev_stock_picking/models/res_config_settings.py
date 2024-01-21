from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_allow_backorder = fields.Boolean(related='company_id.x_allow_backorder', string='Allow backorder', readonly=False)