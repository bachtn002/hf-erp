from odoo import models, fields, api, _


class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    x_is_receive = fields.Boolean("Is receive")
    x_is_done = fields.Boolean("Is done")


