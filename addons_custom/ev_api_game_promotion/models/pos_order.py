# -*- coding: utf-8 -*-

import base64
from odoo import models, api
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def write(self, vals):
        try:
            res = super(PosOrder, self).write(vals)
            if 'state' in vals and vals['state'] == 'paid':
                """
                call api đồng bộ lượt chơi khi đơn hàng có thay đổi số lượt chơi tích lũy
                """
                if self.x_game_turn_reward != 0:
                    sync_game_turn = self.env['sync.game.turn']
                    reward_histories = self.env['game.reward.history'].search([('pos_order_id', '=', self.id)])
                    total_reward = sum(line.game_turn_reward for line in reward_histories)
                    if self.x_game_turn_reward == total_reward:
                        for gcode in reward_histories.mapped('game_code'):
                            reward_by_gcode = 0
                            for line in reward_histories:
                                if line.game_code == gcode:
                                    reward_by_gcode += line.game_turn_reward
                            hash_value = str(self.partner_id.id) + ':' + str(gcode) + ':' + str(reward_histories[0].phone) + ':' + str(reward_by_gcode) + ':' + str(self.pos_reference)
                            value = {
                                'pos_order_ref': self.pos_reference,
                                'campaign_code': gcode,
                                'phone': reward_histories[0].phone,
                                'turn': reward_by_gcode,
                                'partner_id': self.partner_id.id,
                                'hash_value': str(base64.b64encode(bytes(hash_value, 'utf-8')), 'utf-8'),
                                'state': 'draft',
                            }
                            sync_game_turn |= self.env['sync.game.turn'].sudo().create(value)
                    sync_game_turn.action_call_api_sync()
            return res
        except Exception as e:
            raise ValidationError(e)
