odoo.define('ev_pos_online.ProductScreen', function (require) {
    "use strict";

    const models = require('point_of_sale.models');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');


    let ProductScreenOnline = ProductScreen =>
        class extends ProductScreen {
            async _barcodeProductAction(code) {
                var product = this.env.pos.db.get_product_by_barcode(code.base_code);
                if(!product){
                    try {
                        await this.env.pos.search_product_to_server(code.base_code);
                        this.render();
                    } catch (error) {
                        if (error == undefined) {
                            await this.showPopup('OfflineErrorPopup', {
                                title: this.env._t('Offline'),
                                body: this.env._t('Unable to search customer.'),
                            });
                        }
                    }
                }
                super._barcodeProductAction(code);
            }
        }

    Registries.Component.extend(ProductScreen, ProductScreenOnline);

    return ProductScreen;

});