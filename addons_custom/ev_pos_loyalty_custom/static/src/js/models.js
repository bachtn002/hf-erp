odoo.define('ev_pos_loyalty_custom.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    models.load_fields('res.partner', 'x_ecommerce');
    models.load_fields("loyalty.rule", ['product_rule_rule', 'point_per_product', 'category_id','product_cate_rule_rule']);
    return models
});