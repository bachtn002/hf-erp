odoo.define('ev_pos_combo.ProductCombo', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class ProductCombo extends PosComponent {
        get_product_url(product) {
            return window.location.origin + `/web/image?model=product.product&field=image_128&id=${product.id}&write_date=${product.write_date}&unique=1`;
        };

        selectProduct(event) {
            var self = this;
            var $el = $(event.currentTarget);
            var product_id = Number($el.data('product-id'));
            self.scroll_position = Number($el.find('.combo-product-container').scrollTop()) || 0;
            if ($(event.target).hasClass('fa-minus') || $(event.target).hasClass('product-remove')) {
                if ($el.hasClass('selected')) {
                    this.props.record.product_details.map(function (product_detail) {
                        if (product_detail.product_id == product_id) {
                            product_detail.used_time = 0;
                        }
                    });
                }
            } else {
                var added_item = 0;
                this.props.record.product_details.map(function (product_detail) {
                    added_item += product_detail.used_time;
                });
                this.props.record.product_details.map(function (product_detail) {
                    if (product_detail.product_id == product_id) {
                        if (product_detail.no_of_items > product_detail.used_time && product_detail.no_of_items > added_item) {
                            product_detail.used_time += 1;
                        }
                    }
                });
            }
        };
    }

    ProductCombo.template = 'ProductCombo';

    Registries.Component.add(ProductCombo);

    return ProductCombo;
});
