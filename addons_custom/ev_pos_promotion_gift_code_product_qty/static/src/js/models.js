odoo.define('ev_pos_promotion_gift_code_product_qty.models', function (require) {
    "use strict"

    const models = require('point_of_sale.models');

    models.load_models([{
        model: 'gift.code.product.qty.conditions',
        label: 'Promotion Gift code product qty condition',
        fields: ['product_id', 'min_qty', 'promotion_id'],
        domain: (self) => {
            return [['promotion_id', 'in', self.db.getPromotionIds()]]
        },
        loaded: (self, res) => {
            self.db.addGiftCodeProductQtyCondition(res);
        }
    }, {
        model: 'gift.code.product.qty.applies',
        label: 'Promotion Gift code product qty apply',
        fields: ['promotion_gift_id', 'gift_qty', 'promotion_id'],
        domain: (self) => {
            return [['promotion_id', 'in', self.db.getPromotionIds()]]
        },
        loaded: (self, res) => {
            self.db.addGiftCodeProductQtyApplies(res);
        }
    }], {after: 'pos.promotion'});

    return models;

})
