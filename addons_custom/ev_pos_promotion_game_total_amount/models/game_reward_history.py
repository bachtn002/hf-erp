from odoo import api, fields, models


class GameRewardHistory(models.Model):
    _name = 'game.reward.history'
    _description = 'Game Reward History'
    _order = 'id desc'

    pos_promotion_id = fields.Many2one('pos.promotion', "Pos promotion", required=1)
    game_code = fields.Char(related='pos_promotion_id.game_code', string='Game code')
    pos_order_id = fields.Many2one('pos.order', "Pos Order", required=1)
    partner_id = fields.Many2one('res.partner', "Customer", required=1)
    phone = fields.Char("Customer phone number", required=1)
    game_turn_reward = fields.Integer("Game turn reward", default=0)

