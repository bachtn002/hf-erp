odoo.define('ev_pos_combo.ProductScreen', function (require) {
    'use strict';

    const { Gui } = require('point_of_sale.Gui');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const core = require('web.core');
    var _t = core._t;

    let ProductScreenCombo = ProductScreen =>
        class extends ProductScreen {

            async _clickProduct(event) {
                super._clickProduct(event)
                if (this.env.pos.config.x_enable_combo && this.env.pos.config.x_edit_combo && event.detail.x_is_combo) {
                    if (!this.currentOrder) {
                        this.env.pos.add_new_order();
                    }
                    const order = this.currentOrder;
                    this._add_detail_combo(order.orderlines.models[order.orderlines.models.length - 1]);
                    // this.showPopup('PopupCombo', {line: order.orderlines.models[order.orderlines.models.length - 1]});
                }
            }

            _barcodeProductAction(code) {
                super._barcodeProductAction(code);
                var product = this.env.pos.db.get_product_by_barcode(code.base_code);
                if(!product){
                    return false;
                }
                if (this.env.pos.config.x_enable_combo && this.env.pos.config.x_edit_combo && product.x_is_combo) {
                    if (!this.currentOrder) {
                        this.env.pos.add_new_order();
                    }
                    const order = this.currentOrder;
                    this._add_detail_combo(order.orderlines.models[order.orderlines.models.length - 1]);
                }
            }

            _get_combo_products_details(options) {
                var self = this;
                var product = options.product || false;
                var combo_products_details = [];
                var combo_product_info = options.combo_product_info || false;
                if (!product) {
                    return combo_products_details;
                }
                product.x_product_combo_ids.map(function (id) {
                    var record = _.find(self.env.pos.product_combo, function (data) {
                        return data.id === id;
                    });
                    combo_products_details.push(record);
                });
                return combo_products_details;
            }

            _get_new_combo_products_details(combo_products_details) {
                var new_combo_products_details = [];
                combo_products_details.map(function (combo_line) {
                    var details = [];
                    if (combo_line.product_ids.length > 0) {
                        combo_line.product_ids.map(function (product_id) {
                            if (combo_line.require) {
                                var data = {
                                    'no_of_items': combo_line.no_of_items,
                                    'product_id': product_id,
                                    'category_id': combo_line.pos_category_id[0] || false,
                                    'used_time': combo_line.no_of_items,
                                }
                                details.push(data);
                            } else {
                                var data = {
                                    'no_of_items': combo_line.no_of_items,
                                    'product_id': product_id,
                                    'category_id': combo_line.pos_category_id[0] || false,
                                    'used_time': 0
                                }
                                if (self.combo_product_info) {
                                    self.combo_product_info.map(function (line) {
                                        if (combo_line.id == line.id && line.product.id == product_id) {
                                            data['used_time'] = line.qty;
                                        }
                                    });
                                }
                                details.push(data);
                            }
                        });
                        new_combo_products_details.push({
                            'id': combo_line.id,
                            'no_of_items': combo_line.no_of_items,
                            'pos_category_id': combo_line.pos_category_id,
                            'product_details': details,
                            'product_ids': combo_line.product_ids,
                            'require': combo_line.require,
                            'require_one': combo_line.require_one
                        });
                    }
                });
                return new_combo_products_details;
            }

            _add_detail_combo(line) {
                var self = this;
                var order = self.env.pos.get_order();
                var products_info = [];
                var pricelist = order.pricelist;
                let none_require_one = true;
                var combo_products_details = self._get_combo_products_details(line);
                var new_combo_products_details = self._get_new_combo_products_details(combo_products_details);
                new_combo_products_details.map(function (combo_line) {
                    if (combo_line.product_details.length > 0) {
                        combo_line.product_details.map(function (prod_detail) {
                            if (combo_line.require_one && prod_detail.used_time) {
                                none_require_one = false
                            }
                            if (prod_detail.used_time) {
                                var product = self.env.pos.db.get_product_by_id(prod_detail.product_id);
                                if (product) {
                                    products_info.push({
                                        "product": {
                                            'display_name': product.display_name,
                                            'id': product.id,
                                        },
                                        'qty': prod_detail.used_time,
                                        'price': product.get_price(pricelist, 1),
                                        'id': combo_line.id,
                                    });
                                }
                            }
                        });
                    }
                });
                if (none_require_one) {
                    // warning here
                    console.log('none_require_one', none_require_one);
                    // return this.showPopup('PopupWarning');
                }

                var selected_line = order.get_selected_orderline();
                if (products_info.length > 0) {
                    if (selected_line) {
                        selected_line.set_combo_prod_info(products_info);
                    } else {
                        alert("Selected line not found!");
                    }
                } else {
                    if (selected_line) {
                        order.remove_orderline(selected_line);
                        Gui.showPopup('ErrorPopup', {
                            'title': _t('Warning'),
                            'body': _t('Please add enough products for the combo before continuing.'),
                        });
                        return false;
                    }
                }
                order.save_to_db();
            }
        }

    Registries.Component.extend(ProductScreen, ProductScreenCombo);

    return ProductScreen;
});
