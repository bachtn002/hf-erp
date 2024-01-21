odoo.define('ev_pos_promotion_gift_condition.models', function (require) {
    "use strict"

    const models = require('point_of_sale.models');

    models.load_models([{
        model: 'pos.promotion.gift.condition.apply',
        label: 'Promotion Gift condition Apply',
        fields: ['promotion_id', 'category_id', 'product_id', 'qty', 'total_amount'],
        domain: (self) => {
            return [['promotion_id', 'in', self.db.getPromotionIds()]]
        },
        loaded: (self, res) => {
            self.db.addPromotionGiftCondition(res);
        }
    }, {
        model: 'pos.promotion.gift.apply',
        label: 'Promotion Gift apply',
        fields: ['promotion_id', 'category_id', 'product_id', 'qty'],
        domain: (self) => {
            return [['promotion_id', 'in', self.db.getPromotionIds()]]
        },
        loaded: (self, res) => {
            self.db.addPromotionGiftApply(res);
        }
    }], {after: 'pos.promotion'});

    models.load_fields('pos.promotion', ['pos_promotion_gift_condition_ids', 'pos_promotion_gift_apply_ids']);

    return models;

})
