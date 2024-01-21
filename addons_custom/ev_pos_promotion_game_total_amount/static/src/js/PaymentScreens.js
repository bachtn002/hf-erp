odoo.define("ev_pos_promotion_game_total_amount.PaymentScreen", function (require) {
    "use strict";

    const core = require('web.core');
    const { Gui } = require('point_of_sale.Gui');
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    var _t = core._t;

    let PaymentScreenGameReward = PaymentScreen =>
        class extends PaymentScreen {
            async _finalizeValidation() {

                var self = this;
                var order = this.currentOrder;
                if (order.x_game_turn_reward) {
                    order.set_x_game_turn_reward(order.x_game_turn_reward);
                }
                if (order.x_game_turn_rules) {
                    order.set_x_game_turn_rules(order.x_game_turn_rules);
                }
                super._finalizeValidation();
            }
            captureChange(event) {
                this.changes[event.target.name] = event.target.value;
            }

        }

    Registries.Component.extend(PaymentScreen, PaymentScreenGameReward);
    return PaymentScreen;
});