odoo.define('ev_promotion_voucher.ButtonPromotionVoucherDelete', function (require) {
    "use strict"
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const models = require('ev_pos_promotion.Promotion');
    const rpc = require('web.rpc');
    const PosDB = require('point_of_sale.DB');
    class ButtonPromotionVoucherDelete extends PosComponent {
        constructor() {
            super(...arguments);
            this.db = new PosDB;
        }

        async onClick(ev) {
            // ev.preventDefault();
            let data_promotions = this.db.load('promotions');
            this.props.onClickButton(ev);
        }
    }

    ButtonPromotionVoucherDelete.template = 'ButtonPromotionVoucherDelete';
    Registries.Component.add(ButtonPromotionVoucherDelete);

    return ButtonPromotionVoucherDelete
});