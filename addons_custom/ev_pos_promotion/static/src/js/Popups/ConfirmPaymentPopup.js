odoo.define('ev_pos_promotion.ConfirmPaymentPopup', function (require) {
    "use strict"

    const core = require('web.core');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    let _t = core._t;
    let _lt = core._lt;


    class ConfirmPaymentPopup extends AbstractAwaitablePopup {

        /**
         * onClickApplySelected.
         *
         * Áp dụng các promotion đã chọn
         *
         */
        async onClickApplySelected() {
            this.props.resolve({applyAll: false, applySelected: true});
            this.trigger('close-popup');
        }

        /**
         * onClickApplyAll.
         *
         * Áp dụng toàn bộ promotion thoả mã đơn hàn
         *
         */
        async onClickApplyAll() {
            this.props.resolve({applyAll: true, applySelected: false});
            this.trigger('close-popup');
        }

    }

    ConfirmPaymentPopup.template = 'ConfirmPaymentPopup';
    ConfirmPaymentPopup.defaultProps = {
        title: _t('Confirm Payment Popup'),
        body: _t('Apply all promotion or selected promotion'),
        cancelText: _t('Close'),
        applySelectedText: _lt('Apply selected'),
        applyAllText: _lt('Apply all'),
    }

    Registries.Component.add(ConfirmPaymentPopup);

    return ConfirmPaymentPopup;

});
