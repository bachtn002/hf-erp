odoo.define('ev_promotion_voucher.PromotionList', function (require) {

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');


    class PromotionVoucherList extends PosComponent {
        constructor() {
            super(...arguments);
        }
    }

    PromotionVoucherList.template = 'PromotionVoucherList';

    Registries.Component.add(PromotionVoucherList);

    return PromotionVoucherList;

});
