from odoo import api, fields, models


class LoyaltyProgram(models.Model):
    _inherit = 'loyalty.program'

    x_pos_channel_ids = fields.Many2many('pos.channel', 'loyalty_program_pos_channel_rel', 'loyalty_id', 'channel_id', string="Pos channel")

