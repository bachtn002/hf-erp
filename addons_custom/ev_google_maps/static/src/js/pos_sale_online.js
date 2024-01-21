odoo.define("ev_google_maps.pos", function (require) {
    "use strict";


    const { Gui } = require('point_of_sale.Gui');
    var ev_sale_online = require('ev_sale_online.pos');
    var models = require("point_of_sale.models");
    var core = require('web.core');
    var _t = core._t;

    var OrderSupperSaleOnline = models.Order;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            this.x_lat_so = options.lat || '';
            this.x_long_so = options.long || '';
            this.x_receiver_so = options.receiver || '';
            this.x_receiver_phone_so = options.receiver_phone || '';
            this.x_address_delivery_so = options.address_delivery || '';
            this.x_home_delivery_so = options.home_delivery || '';
            this.x_distance_so = options.x_distance || '';
            OrderSupperSaleOnline.prototype.initialize.apply(this, arguments);
            return this;
        },
        init_from_JSON: function (json) {
            this.x_lat_so = json.lat;
            this.x_long_so = json.long;
            this.x_receiver_so = json.receiver;
            this.x_receiver_phone_so = json.receiver_phone;
            this.x_address_delivery_so = json.address_delivery;
            this.x_home_delivery_so = json.home_delivery;
            this.x_distance_so = json.x_distance;
            OrderSupperSaleOnline.prototype.init_from_JSON.call(this, json);
        },
        export_as_JSON: function () {
            var data = OrderSupperSaleOnline.prototype.export_as_JSON.apply(this, arguments);
            data.x_lat_so = this.get_lat();
            data.x_long_so = this.get_long();
            data.x_receiver_so = this.get_receiver();
            data.x_receiver_phone_so = this.get_receiver_phone();
            data.x_address_delivery_so = this.get_address_delivery();
            data.x_home_delivery_so = this.get_home_delivery();
            data.x_distance_so = this.get_x_distance();
            return data;
        },
        export_for_printing: function () {
            let res = OrderSupperSaleOnline.prototype.export_for_printing.apply(this, arguments);
            res.x_lat_so = this.get_lat();
            res.x_long_so = this.get_long();
            res.x_receiver_so = this.get_receiver();
            res.x_receiver_phone_so = this.get_receiver_phone();
            res.x_address_delivery_so = this.get_address_delivery();
            res.x_home_delivery_so = this.get_home_delivery();
            res.x_distance_so = this.get_x_distance();
            return res;
        },

        set_lat: function (lat) {
            this.x_lat_so = lat;
        },
        get_lat: function () {
            return this.x_lat_so;
        },
        set_long: function (long) {
            this.x_long_so = long;
        },
        get_long: function () {
            return this.x_long_so;
        },
        set_receiver: function (receiver) {
            this.x_receiver_so = receiver;
        },
        get_receiver: function () {
            return this.x_receiver_so;
        },
        set_receiver_phone: function (receiver_phone) {
            this.x_receiver_phone_so = receiver_phone;
        },
        get_receiver_phone: function () {
            return this.x_receiver_phone_so;
        },
        set_address_delivery: function (address_delivery) {
            this.x_address_delivery_so = address_delivery;
        },
        get_address_delivery: function () {
            return this.x_address_delivery_so;
        },
        set_home_delivery: function (home_delivery) {
            this.x_home_delivery_so = home_delivery;
        },
        get_home_delivery: function () {
            return this.x_home_delivery_so;
        },
        set_x_distance: function (x_distance) {
            this.x_distance_so = x_distance;
        },
        get_x_distance: function () {
            return this.x_distance_so;
        },
    });


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
                x_source_order_id: get_attr(message, "source_order_id")
            });
            
            // console.log(message);

            if (new_order) {
                // console.log("ORDER",new_order);
                var partner = this.db.search_partner(get_attr(message, "phone"));
                if (partner.length > 0) {
                    new_order.set_client(partner[0])
                } else {
                    var customer = get_attr(message, "partner");
                    if (typeof customer != 'undefined') {
                        self.db.add_partners([customer])
                        var partner = this.db.search_partner(get_attr(message, "phone"));
                        if (partner.length > 0) {
                            new_order.set_client(partner[0])
                        }
                    }

                }


                var orderLines = message.order_line_ids;
                for(var i = 0; i < orderLines.length; i++){
                    var line = orderLines[i];
                    var product = self.db.get_product_by_id(line.product_id);
                    if(typeof product == 'undefined') {
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
                        var new_line = new models.Orderline(
                            {},
                            {pos: self, order: new_order, product: product}
                        );
                        new_line.set_quantity(line.quantity);
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
                                    'display_name': product.display_name,
                                    'id': product.id,
                                },
                                'qty': line.quantity,
                                'price': product.lst_price,
                                'id': line.product_id,
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
});