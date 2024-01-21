odoo.define('ev_pos_promotion_loyalty_point.DB', function (require) {
    "use strict"

    const PosDB = require('point_of_sale.DB');


    PosDB.include({

        addPromotionLoyaltyPoint: function (data) {
            this.save('promotion_loyalty_point', data);
        },

        getPromotionLoyaltyPointByPromotionIds: function (ids) {
            let rows = this.load('promotion_loyalty_point', []);
            return rows.filter((item) => {
                return _.indexOf(ids, item.promotion_id[0]) != -1;
            });
        }

    });

    return PosDB;

});
