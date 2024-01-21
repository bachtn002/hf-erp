odoo.define('ev_pos_promotion_gift_code_product_qty.DB', function (require) {
    "use strict"

    const PosDB = require('point_of_sale.DB');

    PosDB.include({

        addGiftCodeProductQtyCondition: function (conditions) {
            this.save('gift_code_product_qty_condition', conditions);
        },

        getGiftCodeProductQtyCondition: function (promotions) {
            let rows = this.load('gift_code_product_qty_condition', []);
            return rows.filter((item) => {
                return _.indexOf(promotions, item.promotion_id[0]) != -1;
            });
        },

        addGiftCodeProductQtyApplies: function (applies) {
            this.save('gift_code_product_qty_applies', applies);
        },

        getGiftCodeProductQtyApplies: function (promotions) {
            let rows = this.load('gift_code_product_qty_applies', []);
            return rows.filter((item) => {
                return _.indexOf(promotions, item.promotion_id[0]) != -1;
            });
        },

    });

    return PosDB;

});
