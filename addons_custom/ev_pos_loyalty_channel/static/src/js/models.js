odoo.define('ev_pos_loyalty_channel.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    models.load_fields("loyalty.program", ['x_pos_channel_ids']);
    return models
});