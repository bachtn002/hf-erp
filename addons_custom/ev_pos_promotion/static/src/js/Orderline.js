odoo.define('e_pos_promotion.Orderline', function (require) {
    "use strict"

    const models = require('point_of_sale.models');

    let Orderline = models.Orderline;
    models.Orderline = Orderline.extend({

        init_from_JSON: function (json) {
            Orderline.prototype.init_from_JSON.apply(this, arguments);
            this.x_product_promotion = json.x_product_promotion
            this.promotion_id = json.promotion_id;
            this.x_is_price_promotion = json.x_is_price_promotion;
            this.type = json.type;
            this.x_sequence = json.x_sequence;
            this.sequence_promotion = json.sequence_promotion;
            this.amount_promotion_loyalty = json.amount_promotion_loyalty;
            this.amount_promotion_total = json.amount_promotion_total;
            // this.apply_promotion_for_line_ids = json.apply_promotion_for_line_ids;
            if (json.hasOwnProperty('promotion_applied_quantity')) {
                this.promotion_applied_quantity = json.promotion_applied_quantity;
            } else {
                this.promotion_applied_quantity = 0;
            }
        },
        export_as_JSON: function () {
            let res = Orderline.prototype.export_as_JSON.apply(this, arguments);
            res.promotion_id = this.getPromotionId();
            res.x_product_promotion = this.getProductPromotion();
            res.x_is_price_promotion = this.getPricePromotion();
            res.amount_promotion_loyalty = this.getAmountPromotionLoyalty();
            res.amount_promotion_total = this.getAmountPromotionTotal();
            res.x_sequence = this.getx_sequence()
            res.sequence_promotion = this.get_sequence_promotion();
            // res.apply_promotion_for_line_ids = this.getApplyPromotionForLineIds();
            res.promotion_applied_quantity = this.getAppliedPromotionQuantity();
            return res;
        },
        export_for_printing: function () {
            let res = Orderline.prototype.export_for_printing.apply(this, arguments);
            res.promotion_id = this.getPromotionId();
            res.x_sequence = this.getx_sequence()
            res.sequence_promotion = this.get_sequence_promotion();
            // res.apply_promotion_for_line_ids = this.getApplyPromotionForLineIds();
            res.promotion_applied_quantity = this.getAppliedPromotionQuantity();

            return res;
        },
        setPromotion: function (promotionId) {
            this.promotion_id = promotionId;
        },
        setProductPromotion: function (promotionName) {
            this.x_product_promotion = promotionName
        },
        setx_sequence: function (x_sequence) {
            this.x_sequence = x_sequence;
        },
        set_sequence_promotion: function (sequence_promotion) {
            this.sequence_promotion = sequence_promotion;
        },
        setPricePromotion: function (promotionPrice) {
            this.x_is_price_promotion = promotionPrice
        },
        setAmountPromotionLoyalty: function (amount) {
            this.amount_promotion_loyalty = amount;
        },
        setAmountPromotionTotal: function (amount) {
            this.amount_promotion_total = amount;
        },
        getx_sequence: function () {
            if (typeof this.x_sequence === 'number') {
                return this.x_sequence;
            } else if (typeof this.x_sequence === 'object') {
                return this.x_sequence[0];
            }
            else if (typeof this.x_sequence === 'string') {
                return this.x_sequence;
            }
            return false;
        },
        get_sequence_promotion: function () {
            if (typeof this.sequence_promotion === 'number') {
                return this.sequence_promotion;
            } else if (typeof this.sequence_promotion === 'object') {
                return this.sequence_promotion[0];
            }
            else if (typeof this.sequence_promotion === 'string') {
                return this.sequence_promotion;
            }
            return false;
        },
        getPricePromotion: function () {
            if (typeof this.x_is_price_promotion === 'number') {
                return this.x_is_price_promotion;
            } else if (typeof this.x_is_price_promotion === 'object') {
                return this.x_is_price_promotion[0];
            }
            else if (typeof this.x_is_price_promotion === 'string') {
                return this.x_is_price_promotion;
            }
            return false;
        },
        getAmountPromotionLoyalty: function () {
            if (typeof this.amount_promotion_loyalty === 'number') {
                return this.amount_promotion_loyalty;
            } else if (typeof this.amount_promotion_loyalty === 'object') {
                return this.amount_promotion_loyalty[0];
            }
            else if (typeof this.amount_promotion_loyalty === 'string') {
                return this.amount_promotion_loyalty;
            }
            return false;
        },
        getAmountPromotionTotal: function () {
            if (typeof this.amount_promotion_total === 'number') {
                return this.amount_promotion_total;
            } else if (typeof this.amount_promotion_total === 'object') {
                return this.amount_promotion_total[0];
            }
            else if (typeof this.amount_promotion_total === 'string') {
                return this.amount_promotion_total;
            }
            return false;
        },
        getProductPromotion: function () {
            if (typeof this.x_product_promotion === 'string') {
                return this.x_product_promotion;
            } else if (typeof this.x_product_promotion === 'object') {
                return this.x_product_promotion[0];
            }
            return false;
        },
        getPromotionId: function () {
            if (typeof this.promotion_id === 'number') {
                return this.promotion_id;
            } else if (typeof this.promotion_id === 'object') {
                return this.promotion_id[0];
            }
            return false;
        },
        getAppliedPromotionQuantity: function (show) {
            if (show) return 0
            if (this.hasOwnProperty('promotion_applied_quantity')) {
                return this.promotion_applied_quantity;
            }
            return 0
        },

        splitAppliedOrderLine: function () {
            if (this.getAppliedPromotionQuantity() && this.quantity > this.getAppliedPromotionQuantity()) {
                let options = {
                    quantity: this.quantity - this.getAppliedPromotionQuantity(),
                    merge: false,
                }
                this.order.add_product(this.product, options);
                this.set_quantity(this.getAppliedPromotionQuantity())
            }
        }
    });


    return models;
});
