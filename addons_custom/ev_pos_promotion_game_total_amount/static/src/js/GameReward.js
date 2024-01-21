odoo.define('ev_pos_promotion_game_total_amount.OrderWidgetGameReward', function(require) {
'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const utils = require('web.utils');

    const round_pr = utils.round_precision;

    class OrderWidgetGameReward extends PosComponent {
        get_game_turn_reward() {
            if(this.env.pos.get_order){
                return this.env.pos.get_order().x_game_turn_reward
            }
            return 0
        }
        get_game_turn_detail() {
            var message = ''
            if(this.env.pos.get_order){
                var rules = this.env.pos.get_order().x_game_turn_rules
                for(var i =0; i< rules.length; i++){
                    message += rules[i][0].game_code + ': ' + (rules[i][0].game_turn).toString() + '\n'
                }
            }
            return message
        }
    }
    OrderWidgetGameReward.template = 'OrderWidgetGameReward';

    Registries.Component.add(OrderWidgetGameReward);

    return OrderWidgetGameReward;
});
