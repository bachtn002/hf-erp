odoo.define('ev_pos_receipt.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    models.load_fields("pos.config", ['x_address_shop','x_name_shop','x_code_shop']);
    models.load_fields("product.product", ['type']);
    return models
});