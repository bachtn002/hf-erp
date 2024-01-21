odoo.define('ev_promotion_voucher.PromotionItem', function (require) {
    "use strict"

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');


    class PromotionVoucherItem extends PosComponent {
        constructor() {
            super(...arguments);
        }
    }

    PromotionVoucherItem.template = 'PromotionVoucherItem';

    Registries.Component.add(PromotionVoucherItem);

    return PromotionVoucherItem;

})
