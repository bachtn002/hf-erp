odoo.define('ev_pos_promotion_game_total_amount.DB', function (require) {
    "use strict"

    const PosDB = require('point_of_sale.DB');

    PosDB.include({

        addPromotionGameTotalAmount: function (conditions) {
            this.save('game_total_amount', conditions);
        },

        getPromotionGameTotalAmountByPromotionIds: function (ids) {
            let rows = this.load('game_total_amount', []);
            return rows.filter((item) => {
                return _.indexOf(ids, item.promotion_id[0]) != -1;
            });
        },


    });

    return PosDB;

});
