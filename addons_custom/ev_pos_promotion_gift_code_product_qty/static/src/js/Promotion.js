odoo.define('ev_pos_promotion_gift_code_product_qty.Promotion', function (require) {
    "use strict"

    const models = require('ev_pos_promotion_gift_code.Promotion');
    const Promotion = models.Promotion;

    models.Promotion = Promotion.extend({

        isValidOrder: function (order, show) {
            let res = Promotion.prototype.isValidOrder.call(this, order, show);
            if (this.type !== 'gift_code_product_qty') {
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
            let conditions = this.db.getGiftCodeProductQtyCondition([this.id]);
            let applies = this.db.getGiftCodeProductQtyApplies([this.id]);
            let orderProductQty = this.getOrderLineProductsQty(order, show)

            if (conditions.length < 1 || applies.length < 1) {
                return false;
            }
            return this.checkValidOrder(order, conditions, orderProductQty);
        },

        checkValidOrder: function (order, conditions, orderProductQty) {
            let shouldSkip = false;
            let validOrder_condition = false
            conditions.forEach((condition) => {
                if (shouldSkip) {
                    return validOrder_condition;
                }
                let isValidProduct = condition.product_id && orderProductQty[condition.product_id[0]] >= condition.min_qty
                if (isValidProduct) {
                    validOrder_condition = true
                }
                // CTKM điều kiện "hoặc" thì 1 sản phẩm đủ điều kiện về số lượng => đơn đủ điều kiện
                if (this.x_promotion_condition_or) {
                    if (isValidProduct) {
                        shouldSkip = true;
                    }
                }
                // CTKM điều kiện "và" thì 1 sản phẩm k đủ điều kiện về số lượng => đơn k đủ điều kiện
                if (!this.x_promotion_condition_or) {
                    if (!(isValidProduct)) {
                        validOrder_condition = false
                        shouldSkip = true;
                    }
                }
            })
            return validOrder_condition
        },

        applyPromotionToOrder: async function (order) {
            Promotion.prototype.applyPromotionToOrder.call(this, order);
            if (this.type !== 'gift_code_product_qty') {
                return;
            }
            if (!order.get_client()) {
                return;
            }
            if (!this.isValidOrder(order)) {
                return;
            }
            let applies = this.db.getGiftCodeProductQtyApplies([this.id]);
            let rule_valid = []
            let name_promotion = []
            applies.forEach((apply) => {
                rule_valid.push({
                    'promotion_id': apply['promotion_id'][0],
                    'pos_promotion_id': apply['promotion_gift_id'][0],
                    'number_code_give': apply['gift_qty']
                })
                name_promotion.push(apply['promotion_gift_id'][1])
            })

            order.set_rules_valid(rule_valid)
            order.set_x_name_promotion(name_promotion);
        },

        revertAppliedOnOrder: function (order) {
            Promotion.prototype.revertAppliedOnOrder.call(this, order);
            if (this.type !== 'gift_code_product_qty') {
                return;
            }
            order.set_rules_valid([])
            order.set_x_name_promotion([]);
            order.x_base64_image = [];
        },

    });

    return models;

})
