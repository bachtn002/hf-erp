odoo.define('ev_pos_loyalty_custom.ev_pos_loyalty_custom', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var core = require('web.core');
    var utils = require('web.utils');

    var _t = core._t;
    models.load_fields("loyalty.program", ['x_point_cost', 'x_discount_amount', 'product_id','res_partner_id_not_apply', 'res_partner_id_not_apply_group','pos_config_apply']);
    // models.load_models([
    //     {
    //         model: 'loyalty.program',
    //         condition: function (self) {
    //             return self.loyalty;
    //         },
    //         fields: ['x_point_cost', 'x_discount_amount', 'product_id'],
    //         loaded: function (self, rewards_cus) {
    //             rewards_cus.forEach(function (reward_cus) {
    //                 self.loyalty.rewards.push(reward_cus);
    //             });
    //         },
    //     },
    // ])
    var _super = models.Order;
    models.Order = models.Order.extend({
        get_amount_rule_custom: function () {
            return this.pos.loyalty
        },
        apply_reward_custom: function (price_discount) {
            var client = this.get_client();
            var product, product_price, order_total, spendable;
            if (!client) {
                return;
            }
            var rule_program = this.get_amount_rule_custom()
            product = this.pos.db.get_product_by_id(rule_program.product_id[0]);
            if (!product) {
                return;
            }
            let options = {
                price: price_discount * -1,
                quantity: 1,
                merge: true,
                extras: {reward_custom_id: 'reward'},
            };
            this.add_product(product, options);
        },
    });
    return models

});