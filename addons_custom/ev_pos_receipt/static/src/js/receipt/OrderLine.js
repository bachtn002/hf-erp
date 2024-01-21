// odoo.define('ev_pos_receipt.Orderline', function (require) {
//     "use strict"
//
//     const models = require('point_of_sale.models');
//
//     let Orderline = models.Orderline;
//     models.Orderline = Orderline.extend({
//         initialize: function (attr, options) {
//             Orderline.prototype.initialize.apply(this, arguments);
//         },
//         get_product: function () {
//             console.log(this.product)
//             return this.product;
//         },
//     });
//     return models;
// });

odoo.define('ev_pos_receipt.Orderline', function (require) {
    "use strict"

    const models = require('point_of_sale.models');

    let Orderline = models.Orderline;
    models.Orderline = Orderline.extend({
        init_from_JSON: function (json) {
            Orderline.prototype.init_from_JSON.apply(this, arguments);
            this.product_type = json.product_type;
            this.x_is_combo = json.x_is_combo;
        },
        export_as_JSON: function () {
            let res = Orderline.prototype.export_as_JSON.apply(this, arguments);
            return res;
        },
        export_for_printing: function () {
            let res = Orderline.prototype.export_for_printing.apply(this, arguments);
            var product = this.get_product();
            res.product_type = product.type;
            res.x_is_combo = product.x_is_combo;
            return res;
        },
    });
    return models;
});
