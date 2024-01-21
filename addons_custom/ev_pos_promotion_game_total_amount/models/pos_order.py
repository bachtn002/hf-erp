from odoo import fields, models, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    x_game_turn_reward = fields.Integer("Game turn reward")
    x_game_turn_reward_history_ids = fields.One2many('game.reward.history', 'pos_order_id', 'Game reward history')


    @api.model
    def _order_fields(self, ui_order):
        result = super(PosOrder, self)._order_fields(ui_order)
        result['x_game_turn_reward'] = ui_order.get('x_game_turn_reward')
        if len(ui_order.get('x_game_turn_rules')):
            game_turn_reward_history_ids = []
            for rule in ui_order.get('x_game_turn_rules'):
                game_turn_reward_history_ids.append([0, 0, {
                    'partner_id': ui_order.get('partner_id'),
                    'pos_promotion_id': rule[0]['promotion_id'][0],
                    'phone': self.env['res.partner'].browse(ui_order.get('partner_id')).phone,
                    'game_turn_reward': rule[0]['game_turn']
                }])
            result['x_game_turn_reward_history_ids'] = game_turn_reward_history_ids

        return result

    def _prepare_refund_values(self, current_session):
        # When pos order refund created update game turn to negative
        values = super(PosOrder, self)._prepare_refund_values(current_session)
        values.update({'x_game_turn_reward': -self.x_game_turn_reward})
        return values

    def write(self, vals):
        res = super(PosOrder, self).write(vals)
        # create history game reward for refund order
        if 'state' in vals and vals['state'] == 'paid' and self.x_pos_order_refund_id:
            self.create_refund_game_reward_history()
        return res

    def create_refund_game_reward_history(self):
        if self.x_game_turn_reward == 0 or not self.partner_id:
            return
        CustomerGameHistory = self.env['game.reward.history']
        domain = [('pos_order_id', '=', self.x_pos_order_refund_id.id), ('partner_id', '=', self.partner_id.id)]
        game_history = CustomerGameHistory.search(domain)
        if game_history:
            for his in game_history:
                CustomerGameHistory.create({
                    'pos_promotion_id': his.pos_promotion_id.id,
                    'pos_order_id': self.id,
                    'partner_id': his.partner_id.id,
                    'phone': his.phone,
                    'game_turn_reward': -his.game_turn_reward
                })
