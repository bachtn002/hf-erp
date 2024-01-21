odoo.define('ev_pos_promotion_gift_code.Promotion', function (require) {
    "use strict"

    const models = require('ev_pos_promotion.Promotion');
    const rpc = require('web.rpc');
    const ProductScreenCustom = require('ev_pos_ConfirmPaymentPopup_custom.ProductScreenCustom');
    const {Gui} = require('point_of_sale.Gui');
    const Promotion = models.Promotion;
    var core = require('web.core');
    var _t = core._t;

    models.Promotion = Promotion.extend({

        isValidOrder: function (order, show) {
            let res = Promotion.prototype.isValidOrder.call(this, order, show);
            if (this.type !== 'gift_code_total_amount') {
                return res;
            }
            let isValidTime = this.isValidTime()
            if (!isValidTime) {
                return res;
            }
            let isValidPartnerNot = this.isValidPartnerNot(order);
            if (!isValidPartnerNot) {
                return res;
            }
            let isValidPartner = this.isValidPartner(order)
            if (!isValidPartner) {
                return res;
            }
            let conditions = this.db.getPromotionGiftCodeTotalAmountByPromotionIds([this.id]);
            let rule = this.getPromotionApply(order, conditions);
            return rule !== false;
        },

        revertAppliedOnOrder: function (order) {
            Promotion.prototype.revertAppliedOnOrder.call(this, order);
            if (this.type !== 'gift_code_total_amount') {
                return;
            }
            order.set_rules_valid([])
            order.set_x_name_promotion([]);
            order.x_base64_image = [];
        },

        applyPromotionToOrder: async function (order) {
            Promotion.prototype.applyPromotionToOrder.call(this, order);
            if (this.type !== 'gift_code_total_amount') {
                return;
            }
            if (!order.get_client()) {
                return;
            }
            if (!this.isValidOrder(order)) {
                return;
            }
            let conditions = this.db.getPromotionGiftCodeTotalAmountByPromotionIds([this.id]);
            let rule = this.getPromotionApply(order, conditions);
            if (!rule) return;

            let rule_valid = []
            rule_valid.push({
                'promotion_id': rule['promotion_id'][0],
                'pos_promotion_id': rule['promotion_code_id'][0],
                'number_code_give': 1 //tặng 1 code trên 1 CTKM
            })
            order.set_rules_valid(rule_valid)
            order.set_x_name_promotion(rule['promotion_code_id'][1]);
        },

        getPromotionApply: function (order, conditions) {
            let orderAmount = order.get_total_with_tax();
            conditions = conditions.filter((item) => {
                return orderAmount >= item.total_amount
            });
            if (conditions.length < 1) return false;

            for (let i = 0; i < conditions.length - 1; i++) {
                for (let j = i + 1; j < conditions.length; j++) {
                    if (conditions[i].total_amount > conditions[j].total_amount) {
                        let temp = conditions[i];
                        conditions[i] = conditions[j];
                        conditions[j] = temp;
                    }
                }
            }
            return conditions.pop();
        }

    });
    return models;
})