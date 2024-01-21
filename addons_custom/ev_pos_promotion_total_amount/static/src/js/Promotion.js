odoo.define('ev_pos_promotion_total_amount.Promotion', function (require) {
    "use strict"

    const models = require('ev_pos_promotion.Promotion');
    const rpc = require('web.rpc');
    const Promotion = models.Promotion;
    models.Promotion = Promotion.extend({
        applyPromotionToOrder: async function (order) {
            Promotion.prototype.applyPromotionToOrder.call(this, order);
            if (this.type != 'total_amount') {
                return;
            }
            if (!this.isValidOrder(order)) {
                return;
            }
            let rules = this.db.getPromotionTotalAmountByPromotionIds([this.id]);
            let rule = this.filterValidRulePromotionTotalAmount(order, rules);
            if (!rule) {
                return;
            }
            let product = this.db.get_product_by_id(this.product_id[0]);
            if (rule.check_discount_price === 'discount') {
                let amount = rule.discount / 100 * order.get_total_with_tax();
                if (rule.max_discount > 0) {
                    amount = amount <= rule.max_discount ? amount : rule.max_discount;
                }
                let options = {
                    price: amount * -1,
                    quantity: 1,
                    merge: false,
                    extras: {
                        promotion_id: this.id,
                        x_product_promotion: this.name,
                        type : this.type
                    }
                }
                order.add_product(product, options);
                let args = [this.id, this.id];
                await rpc.query({
                    model: 'custom.weekdays',
                    method: 'get_custom_week',
                    args: args,
                }).then(function (data) {
                    console.log('data', data)
                }, function (type, err) {
                    reject();
                });
            }
            if (rule.check_discount_price === 'price') {
                let options = {
                    price: rule.price_discount * -1,
                    quantity: 1,
                    merge: false,
                    extras: {
                        promotion_id: this.id,
                        x_product_promotion: this.name,
                        type : this.type
                    }
                }
                order.add_product(product, options);
                // let count_product_not_km = 0
                // order.orderlines.forEach((line) => {
                //     if (line.promotion_id === undefined) {
                //         count_product_not_km += 1
                //     }
                // })
                // order.orderlines.forEach((line) => {
                //     if (line.promotion_id === undefined) {
                //         line.setProductPromotion(this.name)
                //     }
                // })
            }

        },

        revertAppliedOnOrder: function (order) {
            Promotion.prototype.revertAppliedOnOrder.call(this, order);
            if (this.type != 'total_amount') {
                return;
            }
            order.orderlines.forEach((line) => {
                // Fix when clear promotion;
                if (!line) return;
                if (line.hasOwnProperty('promotion_id')
                    && line['promotion_id'] != undefined) {
                    let promotion_id = line.promotion_id;
                    if (typeof promotion_id !== 'number') {
                        promotion_id = promotion_id[0];
                    }
                    if (!promotion_id) {
                        return
                    }
                    let promotion = self.posmodel.getPromotionById(promotion_id);
                    if (promotion.type == 'total_amount') {
                        order.remove_orderline(line);
                    }
                }
            });
        },

        isValidOrder: function (order, show) {
            let res = Promotion.prototype.isValidOrder.call(this, order, show);
            if (this.type != 'total_amount') {
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
            let rules = this.db.getPromotionTotalAmountByPromotionIds([this.id]);
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
            const getAmount = (order, rule) => {
                let amount = rule.discount / 100 * orderAmount;
                if (rule.max_discount > 0) {
                    amount = amount <= rule.max_discount ? amount : rule.max_discount;
                }
                return amount;
            }
            // rules.sort(function (first, second) {
            //     let x = getAmount(order, first);
            //     let y = getAmount(order, second);
            //     return ((x < y) ? -1 : ((x > y) ? 1 : 0));
            // });
            return rules.pop();
        },

        initFromJson: function (json) {
            Promotion.prototype.initFromJson(json);
            this.pos_promotion_total_amount_ids = json.pos_promotion_total_amount_ids;
        },

        exportToJson: function () {
            let json = Promotion.prototype.exportToJson();
            json.pos_promotion_total_amount_ids = this.pos_promotion_total_amount_ids;
            return json;
        }

    });

    return models;

})
