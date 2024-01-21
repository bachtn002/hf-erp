odoo.define('ev_pos_promotion_gift_code.DB', function (require) {
    "use strict"

    const PosDB = require('point_of_sale.DB');

    PosDB.include({

        addPromotionGiftCodeTotalAmount: function (data) {
            this.save('gift_code_total_amount', data);
        },

        getPromotionGiftCodeTotalAmountByPromotionIds: function (ids) {
            let rows = this.load('gift_code_total_amount', []);
            return rows.filter((item) => {
                return _.indexOf(ids, item.promotion_id[0]) != -1;
            });
        },
    });

    return PosDB;
});