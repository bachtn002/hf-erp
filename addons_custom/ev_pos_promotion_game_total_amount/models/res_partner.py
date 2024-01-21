from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_game_turn_reward_history_ids = fields.One2many('game.reward.history', 'partner_id', 'Game reward history')
