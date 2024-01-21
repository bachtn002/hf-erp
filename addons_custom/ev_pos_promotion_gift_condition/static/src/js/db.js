odoo.define('ev_pos_promotion_gift_condition.DB', function (require) {
    "use strict"

    const PosDB = require('point_of_sale.DB');

    PosDB.include({

        addPromotionGiftCondition: function (conditions) {
            this.save('gift_condition', conditions);
        },

        getPromotionGiftConditionByPromotionIds: function (ids) {
            let rows = this.load('gift_condition', []);
            return rows.filter((item) => {
                return _.indexOf(ids, item.promotion_id[0]) != -1;
            });
        },

        addPromotionGiftApply: function (applies) {
            this.save('gift_apply', applies);
        },

        getPromotionGiftApplyByPromotionIds: function (ids) {
            let rows = this.load('gift_apply', []);
            return rows.filter((item) => {
                return _.indexOf(ids, item.promotion_id[0]) != -1;
            });
        },

    });

    return PosDB;

});
