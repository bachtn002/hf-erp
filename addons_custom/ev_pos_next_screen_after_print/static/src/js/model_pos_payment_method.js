odoo.define('ev_pos_next_screen_after_print.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    models.load_fields('pos.payment.method', 'is_cash_count_zero');
    return models
});