odoo.define('ev_pos_ConfirmPaymentPopup_custom.models', function (require) {
    "use strict";

    let models = require('point_of_sale.models');

    models.load_fields("pos.config", ['x_show_popup_payment_confirm']);

    return models

});