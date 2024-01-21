from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ResConfigCustom(models.TransientModel):
    _inherit = 'res.config.settings'

    x_time_request = fields.Float(related='company_id.x_time_request', string='Request Time ', readonly=False)

    x_time_request_weekend = fields.Float(related='company_id.x_time_request_weekend', string='Request Time Weekend ',readonly=False)
