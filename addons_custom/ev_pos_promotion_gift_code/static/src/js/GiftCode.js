odoo.define('ev_pos_promotion_gift_code.OrderWidgetGiftCode', function (require) {
    'use strict'

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class OrderWidgetGiftCode extends PosComponent {

        get_gift_length_name_promotion() {
            if (this.env.pos.get_order) {
                return this.env.pos.get_order().x_name_promotion.length;
            }
            return 0;
        }

        get_gift_name_promotion() {
            if (this.env.pos.get_order) {
                return this.env.pos.get_order().x_name_promotion;
            }
            return 0;
        }
    }

    OrderWidgetGiftCode.template = 'OrderWidgetGiftCode';
    Registries.Component.add(OrderWidgetGiftCode);
    return OrderWidgetGiftCode;
});