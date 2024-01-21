odoo.define('ev_pos_product_list_screen.models', function (require) {
    "use strict";

    let models = require('point_of_sale.models');

    models.load_fields("pos.config", ['x_show_product_list']);

    return models

});