odoo.define('ev_pos_combo.ProductGroupCombo', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { useState } = owl.hooks;

    class ProductGroupCombo extends PosComponent {
        constructor() {
            super(...arguments);
            this.state = useState({
                name: this.props.name,
                products: this.props.products
            })
        }

        collapseBody(event) {
            var self = this;
            $(event.currentTarget)
                .closest('section.combo-product-section')
                .find('div.combo-product-section-body')
                .slideToggle('500', function () {
                    var hide = $(this).css('display') === 'none';
                    var element = $(event.currentTarget).closest('section.combo-product-section').attr('data-section');
                    if (element === 'require') {
                        self.hideBodyRequire = hide
                    } else {
                        self.hideBodyOption = hide
                    }
                });
            $(event.currentTarget)
                .find('i')
                .toggleClass('fa-angle-down fa-angle-up');
        };
    }

    ProductGroupCombo.template = 'ProductGroupCombo';

    Registries.Component.add(ProductGroupCombo);

    return ProductGroupCombo;
});
