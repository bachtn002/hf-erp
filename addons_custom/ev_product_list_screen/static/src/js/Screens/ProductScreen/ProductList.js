odoo.define('ev_product_list_screen.ProductList', function (require) {
    'use strict';

    const ProductList = require('point_of_sale.ProductList');
    const Registries = require('point_of_sale.Registries');


    let ProductListCustom = ProductList =>
        class extends ProductList {
            get show_list() {
                return this.env.pos.config.x_show_product_list
            }
            get background() {
                let index = _.indexOf(this.props.products, this.product)
                return index % 2
            }

            // get pricelist() {
            //     const current_order = this.env.pos.get_order();
            //     if (current_order) {
            //         return current_order.pricelist;
            //     }
            //     return this.env.pos.default_pricelist;
            // }
            // get price() {
            //     const formattedUnitPrice = this.env.pos.format_currency(
            //         this.product.get_price(this.pricelist, 1),
            //         'Product Price'
            //     );
            //     if (this.product.to_weight) {
            //         return `${formattedUnitPrice}/${
            //             this.env.pos.units_by_id[this.product.uom_id[0]].name
            //         }`;
            //     } else {
            //         return formattedUnitPrice;
            //     }
            // }
        };

    Registries.Component.extend(ProductList, ProductListCustom);

    return ProductList;
});
