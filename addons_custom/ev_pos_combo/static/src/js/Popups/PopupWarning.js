odoo.define('ev_pos_combo.PopupWarning', function (require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class PopupWarning extends AbstractAwaitablePopup {

    }

    PopupWarning.template = 'PopupWarning';

    Registries.Component.add(PopupWarning);

    return PopupWarning;
});
