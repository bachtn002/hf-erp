odoo.define('ev_pos_promotion_game_total_amount.Promotion', function (require) {
    "use strict"

    // const OrderWidgetGameReward = require('ev_pos_promotion_game_total_amount.OrderWidgetGameReward');
    const models = require('ev_pos_promotion.Promotion');
    const rpc = require('web.rpc');
    const Promotion = models.Promotion;
    models.Promotion = Promotion.extend({
        applyPromotionToOrder: async function (order) {
            Promotion.prototype.applyPromotionToOrder.call(this, order);
            if (this.type !== 'game_total_amount') {
                return;
            }
            if(!order.get_client()){
                order.set_x_game_turn_reward(0);
                order.set_x_game_turn_rules([])
                return;
            }
            if (!this.isValidOrder(order)) {
                return;
            }
            let rules = this.db.getPromotionGameTotalAmountByPromotionIds([this.id]);
            let rule = this.filterValidRulePromotionTotalAmount(order, rules);
            if (!rule) {
                return;
            }
            //save
            if (rule.game_turn > 0){
                // OrderWidgetGameReward.get_game_turn_reward()
                order.set_x_game_turn_reward(rule.game_turn);
                order.set_x_game_turn_rules([rule])
            }

        },

        revertAppliedOnOrder: function (order) {
            Promotion.prototype.revertAppliedOnOrder.call(this, order);
            if (this.type !== 'game_total_amount') {
                return;
            }
            order.set_x_game_turn_reward(0);
            order.set_x_game_turn_rules([])
        },

        isValidOrder: function (order, show) {
            let res = Promotion.prototype.isValidOrder.call(this, order, show);
            if (this.type !== 'game_total_amount') {
                return res;
            }
            let isValidTime = this.isValidTime()
            if (!isValidTime) {
                return res
            }
            // check partner for not apply promotion
            let isValidPartnerNot = this.isValidPartnerNot(order);
            if (!isValidPartnerNot) {
                return res
            }
            // check partner for apply promotion
            let isValidPartner = this.isValidPartner(order)
            if (!isValidPartner) {
                return res
            }
            let rules = this.db.getPromotionGameTotalAmountByPromotionIds([this.id]);
            let rule = this.filterValidRulePromotionTotalAmount(order, rules);
            return rule != false;
        },

        filterValidRulePromotionTotalAmount: function (order, rules) {
            let orderAmount = order.get_total_with_tax();
            rules = rules.filter((item) => {
                return orderAmount >= item.total_amount;
            });
            if (rules.length < 1) {
                return false;
            }
            return rules.pop();
        },

        // initFromJson: function (json) {
        //     console.log("init form json")
        //     Promotion.prototype.initFromJson(json);
        //     this.promotion_game_total_amount_ids = json.promotion_game_total_amount_ids;
        // },
        //
        // exportToJson: function () {
        //     console.log("export to json ")
        //     let json = Promotion.prototype.exportToJson();
        //     json.promotion_game_total_amount_ids = this.promotion_game_total_amount_ids;
        //     return json;
        // }

    });

    return models;

})
