
odoo.define('ev_pos_promotion_qty_price.DB', function (require) {
    "use strict"

    const PosDB = require('point_of_sale.DB');


    PosDB.include({

        addPromotionQuantityPrice: function (data) {
            this.save('pos_promotion_qty_price', data);
        },

        getPromotionQuantityPriceByPromotionIds: function (ids) {
            let rows = this.load('pos_promotion_qty_price', []);
            return rows.filter((item) => {
                return _.indexOf(ids, item.promotion_id[0]) != -1;
            });
        }

    });

    return PosDB;

});
