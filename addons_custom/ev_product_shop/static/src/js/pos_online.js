odoo.define("ev_product_shop.pos_online", function(require) {
    "use strict";

    var models = require("point_of_sale.models");
    var _super_pos_online = models.PosModel.prototype;

    let PosModel = models.PosModel;
    models.PosModel = PosModel.extend({
        //search new product added to shop (from backend) of current session
        prepare_name_product_domain: function (){
            var domain = _super_pos_online.prepare_name_product_domain()
            if (this.config_id) {
                domain.unshift(['x_pos_shop_ids', 'in', this.config.x_pos_shop_id[0]]);
                domain.unshift('&');
            }else{
                domain.unshift(['id', 'in', []]);
                domain.unshift('&');
            }
            return domain;
        },
    })
});