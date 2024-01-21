odoo.define('ev_pos_promotion_discount_condition.Orderline', function (require) {
    "use strict"

    const models = require('point_of_sale.models');


    const Orderline = models.Orderline;
    models.Orderline = Orderline.extend({

        can_be_merged_with: function (orderline) {
            if (orderline.discount > 0) {
                return false;
            }
            return Orderline.prototype.can_be_merged_with.call(this, orderline);
        }

    });

    return models;

});
