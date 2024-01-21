odoo.define("ev_product_shop.PosModel", function(require) {
    "use strict";

    var models = require("point_of_sale.models");
    var PosModelSuper = models.PosModel.prototype;

    models.PosModel = models.PosModel.extend({
        load_server_data: function () {
            var self = this;
            var loaded = PosModelSuper.load_server_data.call(this);

            //find model product to modify loader arguments (domain and load extra fields)
            var prod_model = _.find(this.models, function (model) {
                return model.model === "product.product";
            });

            if (prod_model) {
                // Load additional field
                prod_model.fields.push("x_pos_shop_ids");

                var custom_domain = prod_model.domain;
                prod_model.domain = function (that) {
                    // var domain = custom_domain(that);
                    var domain = [];
                    //load all products belong to current shop otherwise list products is empty
                    if (self.config_id) {
                        domain = ['&', '&', ['sale_ok', '=', true], ['available_in_pos', '=', true], '|',['x_pos_shop_ids', 'in', self.config.x_pos_shop_id[0]],['type', '=', 'service'] , '|',['company_id', '=', self.config.company_id[0]], ['company_id', '=', false]];
                    }else{
                        domain = [];
                    }
                    return domain;
                };
                return loaded;
            }
        },
    })
});