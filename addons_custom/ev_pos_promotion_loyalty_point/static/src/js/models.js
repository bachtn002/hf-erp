odoo.define('ev_pos_promotion_loyalty_point.models', function (require) {
    "use strict"

    let models = require('point_of_sale.models');


    models.load_models([{
        model: 'pos.promotion.loyalty.point',
        label: 'Promotion loyalty point',
        fields: ['promotion_id', 'total_amount', 'loyalty_point'],
        domain: (self) => {
            return [['promotion_id', '=', self.db.getPromotionIds()]]
        },
        loaded: (self, res) => {
            self.db.addPromotionLoyaltyPoint(res);
        }
    }], {after: 'pos.promotion'});

    models.load_fields('pos.promotion', ['is_miniapp_member', 'pos_promotion_loyalty_point_ids']);
    models.load_fields('pos.order', ['x_is_miniapp_member', 'x_note_member_app']);

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this,arguments);
            var value_note = {}
            if (this.x_is_miniapp_member && this.x_note_member_app)     value_note['code'] = this.x_note_member_app
            if (this.get_points_promotion_loyalty())     value_note['points'] = this.get_points_promotion_loyalty()
            json.x_note_member_app = JSON.stringify(value_note);
            return json;
        },
    });

    return models;

});
