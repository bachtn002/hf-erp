odoo.define('ev_multi_barcode.ProductScreen', function (require) {
    'use strict';

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useRef } = owl.hooks;


    let ProductScreenMultiBarcode = ProductScreen =>
        class extends ProductScreen {
            async _clickProduct(event) {
                this.searchWordInput = useRef('search-word-input');
                const product = event.detail;
                var search_word = this.env.pos.db.search_word
                // search product with exact barcode string if exist product appropriate then add quantity is quantity configured in multi barcode
                var product_barcode = this.env.pos.db.get_barcode_by_string(search_word)
                if (typeof product_barcode === 'undefined'){
                    super._clickProduct(event)
                } else{
                    if (product.id === product_barcode.product_id[0]) {
                        if (!this.currentOrder) {
                            this.env.pos.add_new_order();
                        }
                        const order = this.currentOrder;
                        order.add_product(product, {
                            quantity: parseFloat(product_barcode.qty)
                        });
                    } else {
                        super._clickProduct(event)
                    }
                }
            }
        }

    Registries.Component.extend(ProductScreen, ProductScreenMultiBarcode);

    return ProductScreen;
});
