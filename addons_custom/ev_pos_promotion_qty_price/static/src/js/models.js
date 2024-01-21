odoo.define('ev_pos_promotion_qty_price.models', function (require) {
    "use strict"

    let models = require('point_of_sale.models');

    models.load_models([{
        model: 'pos.promotion.qty.price',
        label: 'Promotion Quantity price',
        fields: ['promotion_id', 'category_id', 'product_id', 'qty', 'price_unit','discount','check_discount_price'],
        domain: (self) => {
            return [['promotion_id', 'in', self.db.getPromotionIds()]]
        },
        loaded: (self, res) => {
            self.db.addPromotionQuantityPrice(res);
        }
    }], {after: 'pos.promotion'});

    models.load_fields('pos.promotion', ['pos_promotion_qty_price_ids']);

    return models;

});
