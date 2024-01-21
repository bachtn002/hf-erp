odoo.define('ev_pos_promotion_loyalty_point.Promotion', function (require) {
    "use strict"

    const models = require('ev_pos_promotion.Promotion');
    const rpc = require('web.rpc');
    var utils = require('web.utils');

    var round_pr = utils.round_precision;
    const Promotion = models.Promotion;
    models.Promotion = Promotion.extend({
        applyPromotionToOrder: function (order) {
            Promotion.prototype.applyPromotionToOrder.call(this, order);
            if (this.type !== 'loyalty_point') {
                return;
            }
            if (!this.isValidOrder(order)) {
                return;
            }
            let total_point = 0
            let orderAmount = order.get_total_with_tax();
            let rules = this.db.getPromotionLoyaltyPointByPromotionIds([this.id]);
            let rule = this.filterValidRulePromotionLoyaltyPoint(order, rules);
            if (rule) {
                total_point += round_pr(orderAmount / rule.total_amount, 1) * rule.loyalty_point;
            }

            order.set_x_promotion_loyalty_point(total_point);
        },

        revertAppliedOnOrder: function (order) {
            Promotion.prototype.revertAppliedOnOrder.call(this, order);
            if (this.type != 'loyalty_point') {
                return;
            }
            order.set_x_promotion_loyalty_point(0);
        },

        isValidOrder: function (order, show) {
            if(this.is_miniapp_member){
                if(!order.x_is_miniapp_member){
                    return
                }
            }

            let res = Promotion.prototype.isValidOrder.call(this, order, show);
            if (this.type != 'loyalty_point') {
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
            let rules = this.db.getPromotionLoyaltyPointByPromotionIds([this.id]);
            let rule = this.filterValidRulePromotionLoyaltyPoint(order, rules);
            return rule != false;
        },

        filterValidRulePromotionLoyaltyPoint: function (order, rules) {
            let orderAmount = order.get_total_with_tax();
            rules = rules.filter((item) => {
                return orderAmount >= item.total_amount;
            });
            if (rules.length < 1) {
                return false;
            }

            return rules.pop();
        },

        initFromJson: function (json) {
            Promotion.prototype.initFromJson(json);
            this.pos_promotion_loyalty_point_ids = json.pos_promotion_loyalty_point_ids;
            this.is_miniapp_member = json.is_miniapp_member;
        },

        exportToJson: function () {
            let json = Promotion.prototype.exportToJson();
            json.pos_promotion_loyalty_point_ids = this.pos_promotion_loyalty_point_ids;
            json.is_miniapp_member = this.is_miniapp_member;
            return json;
        }

    });

    return models;

})
