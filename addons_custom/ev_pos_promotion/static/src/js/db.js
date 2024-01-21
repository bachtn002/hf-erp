odoo.define('ev_pos_promotion.DB', function (require) {
    "use strict"

    const PosDB = require('point_of_sale.DB');


    PosDB.include({

        /**
         * addPromotions
         *
         * Hàm lưu promotions vào store
         *
         * @param {} promotions
         */
        addPromotions: function (promotions) {
            this.save('promotions', promotions);
        },

        /**
         * getPromotionIds.
         *
         * Lâý về danh sách promotion id
         *
         */
        getPromotionIds: function () {
            let promotions = this.load('promotions', []);
            return promotions.map((item) => {
                return item.id;
            });
        },
        addCustomWeekdays: function (day) {
            this.save('day', day)
        },
        getDayIds: function () {
            let day = this.load('day', []);
            return day.map((item) => {
                return item.id;
            });
        },
        getDays: function () {
            let day = this.load('day', []);
            return day.map((item) => {
                return item
            });
        },
        getDayById: function (id) {
            let day = this.getDayIds();
            let res = day.filter((item) => {
                return item.id === id;
            });
            if (res.length > 0)
                return res[0];
            return {};
        },
    });

    return PosDB;

});
