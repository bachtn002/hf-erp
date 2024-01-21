odoo.define('ev_pos_promotion_total_amount.DB', function (require) {
    "use strict"

    const PosDB = require('point_of_sale.DB');


    PosDB.include({

        addPromotionTotalAmount: function (data) {
            this.save('promotion_total_amount', data);
        },

        getPromotionTotalAmountByPromotionIds: function (ids) {
            let rows = this.load('promotion_total_amount', []);
            return rows.filter((item) => {
                return _.indexOf(ids, item.promotion_id[0]) != -1;
            });
        }

    });

    return PosDB;

});
