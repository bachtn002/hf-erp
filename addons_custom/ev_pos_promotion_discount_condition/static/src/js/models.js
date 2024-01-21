odoo.define('ev_pos_promotion_discount_condition.models', function (require) {
    "use strict"

    const models = require('point_of_sale.models');

    models.load_models([{
        model: 'pos.promotion.discount.condition',
        label: 'Promotion discount condition',
        fields: ['promotion_id', 'category_id', 'product_id', 'qty', 'total_amount'],
        domain: (self) => {
            return [['promotion_id', 'in', self.db.getPromotionIds()]]
        },
        loaded: (self, res) => {
            self.db.addPromotionDiscountCondition(res);
        }
    }, {
        model: 'pos.promotion.discount.apply',
        label: 'Promotion discount apply',
        fields: ['promotion_id', 'category_id', 'product_id', 'discount', 'apply_type','price_unit'],
        domain: (self) => {
            return [['promotion_id', 'in', self.db.getPromotionIds()]]
        },
        loaded: (self, res) => {
            self.db.addPromotionDiscountApply(res);
        }
    }], {after: 'pos.promotion'});

    models.load_fields('pos.promotion', ['promotion_discount_condition_ids', 'promotion_discount_apply_ids']);

    return models;

})
