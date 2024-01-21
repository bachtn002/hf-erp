odoo.define('ev_pos_channel.pos', function (require) {
    'use strict'

    var models = require('point_of_sale.models')
    var ev_google_maps = require('ev_google_maps.pos')
    const { Gui } = require('point_of_sale.Gui')
    var core = require('web.core');
    var _t = core._t;


    var PosModelSuper = models.PosModel;
    models.PosModel = models.PosModel.extend({
        initialize: function () {
            var self = this;
            PosModelSuper.prototype.initialize.apply(this, arguments);
            this.ready.then(function () {
                var channel_name = "pos.sale_online";
                var callback = self.sync_from_server_callback;
                self.bus.add_channel_callback(channel_name, callback, self);
            });
        },

        sync_from_server_callback: function (message) {
            var self = this;
            var get_attr = function (obj, attr) {
                return obj[attr] || (obj.data && obj.data[attr]);
            };

            var config_id = get_attr(message, "pos_config_id")
            if (this.config_id !== config_id) {
                return;
            }
            if (this._order_online_exit(get_attr(message, "name"))) {
                return;
            }
            var new_order = this.so_create_order({
                sale_online: get_attr(message, "name"),
                note_sale_online: get_attr(message, "note"),
                lat: get_attr(message, "lat"),
                long: get_attr(message, "long"),
                receiver: get_attr(message, "receiver"),
                receiver_phone: get_attr(message, "receiver_phone"),
                address_delivery: get_attr(message, "address_delivery"),
                home_delivery: get_attr(message, "home_delivery"),
                x_distance: get_attr(message, "x_distance"),
                x_source_order_id: get_attr(message, "source_order_id"),
                x_id_pos_channel_sale_online: get_attr(message, "pos_channel_id"),
                is_created_by_api: get_attr(message, "is_created_by_api"),
                loyalty_point_redeem: get_attr(message, "loyalty_point_redeem"),
                payment_info_sale_online: get_attr(message, "payment_info"),
                x_buyer_not_get_invoice: get_attr(message, "buyer_not_get_invoice"),
                x_sinvoice_vat: get_attr(message, "sinvoice_vat"),
                x_sinvoice_company_name: get_attr(message, "sinvoice_company_name"),
                x_sinvoice_address: get_attr(message, "sinvoice_address"),
                x_sinvoice_email: get_attr(message, "sinvoice_email"),
                order_line_info: get_attr(message, "order_line_info"),
                discount_on_bill: get_attr(message, "discount_on_bill"),
                discount_on_product: get_attr(message, "discount_on_product"),
                write_date: get_attr(message, "write_date"),
                id_sale_online: get_attr(message, "id_sale_online"),
                state_sale_online: get_attr(message, "state_sale_online"),
                total_discount_on_bill: get_attr(message, "total_discount_on_bill"),
                product_km_id: get_attr(message, "product_km_id"),
            });
            if (new_order) {
                var customer = get_attr(message, "partner");
                if (typeof customer != 'undefined') {
                    self.db.add_partners([customer])
                    var partner = this.db.get_partner_by_id(customer.id);
                    if (typeof partner != 'undefined') {
                        new_order.set_client(partner)
                    }
                }


                var orderLines = message.order_line_ids;
                for (var i = 0; i < orderLines.length; i++) {
                    var line = orderLines[i];
                    var product = self.db.get_product_by_id(line.product_id);
                    if (typeof product == 'undefined') {
                        Gui.showPopup('ErrorPopup', {
                            title: _t('Thông báo'),
                            body: _t('Trong đơn hàng có sản phẩm không được phép bán trong đơn ' + get_attr(message, "name")),
                        });
                        return false;
                    }
                }
                var arr_product_combo_info = []
                orderLines.forEach(function (line) {
                    if (!line.sale_online_id) {
                        let product = self.db.get_product_by_id(line.product_id)
                        arr_product_combo_info.push(line)
                    } else {
                        var product = self.db.get_product_by_id(line.product_id);
                        if (typeof product == 'undefined') {
                            var using_company_currency = self.config.currency_id[0] === self.company.currency_id[0];
                            var conversion_rate = self.currency.rate / self.company_currency.rate;
                            self.db.add_products(_.map(line.product, function (product) {
                                if (!using_company_currency) {
                                    product.lst_price = round_pr(product.lst_price * conversion_rate, self.currency.rounding);
                                }
                                product.categ = _.findWhere(self.product_categories, {'id': product.categ_id[0]});
                                product.pos = self;
                                return new models.Product({}, product);
                            }));
                            product = self.db.get_product_by_id(line.product_id);
                        }
                        var new_line = new models.Orderline({}, {pos: self, order: new_order, product: product});
                        new_line.set_quantity(line.quantity);
                        if (new_order.is_created_by_api)
                            new_line.price = line.price
                        new_order.orderlines.add(new_line, {not_render: true});
                    }
                });
                this.get("orders").add(new_order);
                var products_info = [];
                new_order.orderlines.models.forEach((model) => {
                    arr_product_combo_info.forEach((line) => {
                        //nếu sản phẩm có parent là SP combo trong model thì đẩy vào product_info[]
                        if (line.product_combo_parent === model.product.product_tmpl_id) {
                            let product = self.db.get_product_by_id(line.product_id)
                            products_info.push({
                                "product": {
                                    'display_name': product.display_name, 'id': product.id,
                                }, 'qty': line.quantity, 'price': product.lst_price, 'id': line.product_id,
                            });
                        }
                    })
                    if (products_info.length > 0) {
                        model.set_combo_prod_info(products_info);
                        products_info = [];
                    }
                })
            }
        },

        sync_list_order: function (orders) {
            for (var i = 0; i < orders.length; i++) {
                var order = orders[i];
                this.sync_from_server_callback(order);
            }
        },

        _order_online_exit: function (sale_online) {
            var orders = this.get_order_list();
            var result = false;
            orders.forEach(function (order) {
                if (order.sale_online == sale_online) {
                    result = true;
                }
            });
            return result;
        },

        so_create_order: function (options) {
            options = _.extend({pos: this}, options || {});
            var order = new models.Order({}, options);
            return order;
        },

        _get_field_product: function () {
            var self = this;
            var fields = _.find(self.models, function (model) {
                return model.model === 'product.product';
            }).fields;
            return fields;
        },
    });
})
