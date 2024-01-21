odoo.define('ev_promotion_voucher_custom.models', function (require) {
    "use strict"

    const models = require('point_of_sale.models');

    models.load_fields('pos.promotion',
        ['x_promotion_code_type', 'x_allow_apply_with_other']
    );
    return models;

});
