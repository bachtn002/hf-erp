odoo.define('ev_promotion_voucher.Orderline', function (require) {
    "use strict"

    const models = require('point_of_sale.models');

    let Orderline = models.Orderline;
    models.Orderline = Orderline.extend({
        init_from_JSON: function (json) {
            Orderline.prototype.init_from_JSON.apply(this, arguments);
            this.promotion_code = json.promotion_code;
        },
        export_as_JSON: function () {
            let res = Orderline.prototype.export_as_JSON.apply(this, arguments);
            res.promotion_code = this.getPromotionCode();
            return res;
        },
        export_for_printing: function () {
            let res = Orderline.prototype.export_for_printing.apply(this, arguments);
            res.promotion_code = this.getPromotionCode();
            return res;
        },
        setPromotionCode: function (promotion_code) {
            this.promotion_code = promotion_code;
        },
        getPromotionCode: function () {
            if (typeof this.promotion_code === 'string') {
                return this.promotion_code;
            } else if (typeof this.promotion_code === 'object') {
                return this.promotion_code[0];
            }
            return false;
        },
    })
});