odoo.define('e_pos_promotion.Order', function (require) {
    "use strict"

    const models = require('point_of_sale.models');

    let Order = models.Order;
    models.Order = Order.extend({
        get_name: function () {
            this.name = this.uid
            if (this.name.search('ng ') > 0) {
                this.name = this.name.replace('ng ', ' ');
            }
            return this.name;
        },
    });

    return models;
});