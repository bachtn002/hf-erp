odoo.define('ev_pos_combo.ProductItem', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');


    class ProductItemCombo extends PosComponent {

        get isCombo() {
            return this.props.product.x_is_combo && this.props.product.x_product_combo_ids.length > 0 &&
                this.env.pos.config.x_enable_combo
        }
    }

    ProductItemCombo.template = 'ProductItemCombo';

    Registries.Component.add(ProductItemCombo);

    return ProductItemCombo;
});
