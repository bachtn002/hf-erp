odoo.define('ev_pos_promotion_total_amount.models', function (require) {
    "use strict"

    let models = require('point_of_sale.models');


    models.load_models([{
        model: 'pos.promotion.total.amount',
        label: 'Promotion amount total',
        fields: ['promotion_id', 'total_amount', 'discount', 'max_discount', 'price_discount','check_discount_price'],
        domain: (self) => {
            return [['promotion_id', '=', self.db.getPromotionIds()]]
        },
        loaded: (self, res) => {
            self.db.addPromotionTotalAmount(res);
        }
    }], {after: 'pos.promotion'});

    models.load_fields('pos.promotion', ['pos_promotion_total_amount_ids']);

    return models;

});
