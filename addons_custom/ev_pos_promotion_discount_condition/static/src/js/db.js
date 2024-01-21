odoo.define('ev_pos_promotion_discount_condition.DB', function (require) {
    "use strict"

    const PosDB = require('point_of_sale.DB');

    PosDB.include({

        addPromotionDiscountCondition: function (conditions) {
            this.save('discount_condition', conditions);
        },

        getPromotionDiscountConditionByPromotionIds: function (ids) {
            let rows = this.load('discount_condition', []);
            return rows.filter((item) => {
                return _.indexOf(ids, item.promotion_id[0]) != -1;
            });
        },

        addPromotionDiscountApply: function (applies) {
            this.save('discount_apply', applies);
        },

        getPromotionDiscountApplyByPromotionIds: function (ids) {
            let rows = this.load('discount_apply', []);
            return rows.filter((item) => {
                return _.indexOf(ids, item.promotion_id[0]) != -1;
            });
        },


    });

    return PosDB;

});
