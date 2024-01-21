odoo.define('ev_multi_barcode.product_barcode', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    // Load additional field
    // models.load_fields('product.product', 'x_barcode_ids');

    // Load additional models
    models.load_models([{
        model: 'product.barcode',
        label: 'Multi barcode',
        fields: ['name', 'qty', 'product_id'],
        domain: (self) => {
            var list_product = Object.keys(self.db.product_by_id).map(i=>Number(i))
            return [['active', '=', true], ['product_id', 'in', list_product]]
        },
        loaded: function(self, barcodes) {
            self.db.save_multi_barcode(barcodes)
        }
    }]);

    models.PosModel = models.PosModel.extend({
        scan_product: function (parsed_code) {
            // override method to search multi barcode of product and add corresponding quantity into order

            var selectedOrder = this.get_order();
            var product = this.db.get_product_by_barcode(parsed_code.base_code);
            if (!product) {
                var barcode = this.db.get_barcode_by_string(parsed_code.base_code);
                if (!barcode){
                    return false;
                }
                product = this.db.get_product_by_id(barcode.product_id[0])
                selectedOrder.add_product(product, {quantity: parseFloat(barcode.qty)});
                return true;
            }
            if (parsed_code.type === 'price') {
                selectedOrder.add_product(product, {price: parsed_code.value});
            } else if (parsed_code.type === 'weight') {
                selectedOrder.add_product(product, {quantity: parsed_code.value, merge: true});
            } else if (parsed_code.type === 'discount') {
                selectedOrder.add_product(product, {discount: parsed_code.value, merge: false});
            } else {
                selectedOrder.add_product(product);
            }
            return true;
        },
    })

});