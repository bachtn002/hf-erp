odoo.define('ev_pos_combo.models', function (require) {
    "use strict";

    let models = require('point_of_sale.models');

    let product_fields = ['type', 'x_is_combo', 'x_product_combo_ids', 'lst_price', 'write_date'];

    models.load_fields("product.product", product_fields);

    models.PosModel.prototype.models.push({
        model: 'product.combo',
        loaded: function (self, product_combo) {
            self.product_combo = product_combo;
        },
    });

    var orderline_super = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            let initOptions = {};
            if (options.hasOwnProperty('json')) {
                initOptions = options.json;
            } else if (options.hasOwnProperty('product')) {
                initOptions = options.product;
            }
            if(typeof initOptions != 'undefined'){
                this.combo_prod_info = initOptions.hasOwnProperty('combo_prod_info') ? initOptions.combo_prod_info : [];
                this.x_is_combo = initOptions.hasOwnProperty('x_is_combo') ? initOptions.x_is_combo : false;
            } else {
                this.combo_prod_info = [];
                this.x_is_combo = false;
            }
            orderline_super.initialize.call(this, attr, options);
        },

        // inherit for getting combo_prod_info in order receipt
        export_for_printing: function () {
            var vals = orderline_super.export_for_printing.apply(this);
            vals.combo_prod_info = this.get_combo_prod_info();
            return vals
        },
        // inherit for merging combo with same product info
        can_be_merged_with: function (orderline) {
            var res = orderline_super.can_be_merged_with.call(this, orderline);
            // var _this_combo_prod_ids = [];
            // var _ol_combo_prod_ids = [];
            // this.combo_prod_info.forEach(function (_prod) {
            //     _this_combo_prod_ids.push(_prod.product.id);
            // });
            // orderline.combo_prod_info.forEach(function (prod) {
            //     _ol_combo_prod_ids.push(prod.product.id)
            // });
            // var combo_equal = JSON.stringify(_this_combo_prod_ids.sort()) === JSON.stringify(_ol_combo_prod_ids.sort());
            // if (orderline.x_is_combo && this.pos.config.x_enable_combo && !combo_equal) {
            //     return false;
            // }
            return res;
        },

        set_combo_prod_info: function (combo_prod_info) {
            this.combo_prod_info = combo_prod_info;
            this.trigger('change', this);
        },
        get_combo_prod_info: function () {
            return this.combo_prod_info;
        },
        has_combo_prod_info: function () {
            if (this.combo_prod_info && this.combo_prod_info.length > 0) {
                return true;
            }
            return false;
        },
        export_as_JSON: function () {
            var lines = orderline_super.export_as_JSON.apply(this);
            var combo_ext_line_info = [];
            if (this.product.x_is_combo && this.combo_prod_info && this.combo_prod_info.length > 0) {
                _.each(this.combo_prod_info, function (item) {
                    combo_ext_line_info.push([0, 0, {
                        'product_id': item.product.id,
                        'qty': item.qty,
                        'price': item.price
                    }]);
                });
            }
            lines.x_is_combo = this.x_is_combo;
            lines.combo_prod_info = this.combo_prod_info ? this.combo_prod_info : [];
            lines.combo_ext_line_info = (this.product.x_is_combo ? combo_ext_line_info : []);
            lines.tech_combo_data = (this.product.x_is_combo ? this.combo_prod_info : []);
            lines.is_combo_line = this.combo_prod_info ? true : false
            return lines;
        },
    });

    return models

});