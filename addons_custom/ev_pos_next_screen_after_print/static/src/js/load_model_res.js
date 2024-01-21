odoo.define('ev_pos_next_screen_after_print.models_date_of_birth', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    models.load_fields('res.partner', 'date_of_birth');
    return models
});