odoo.define("ev_sale_online.pos", function (require) {
    "use strict";

    const { Gui } = require('point_of_sale.Gui');
    var models = require("point_of_sale.models");
    var core = require('web.core');
    var _t = core._t;

    var OrderSupper = models.Order;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            this.sale_online = options.sale_online || '';
            this.note = options.note || '';
            this.note_sale_online = options.note_sale_online || '';
            OrderSupper.prototype.initialize.apply(this, arguments);
            return this;
        },
        init_from_JSON: function (json) {
            this.sale_online = json.sale_online;
            this.note = json.note;
            this.note_sale_online = json.note_sale_online;
            OrderSupper.prototype.init_from_JSON.call(this, json);
        },
        export_as_JSON: function () {
            var data = OrderSupper.prototype.export_as_JSON.apply(this, arguments);
            data.sale_online = this.get_sale_online();
            data.note = this.get_note();
            data.note_sale_online = this.get_note_sale_online();
            return data;
        },
        export_for_printing: function () {
            let res = OrderSupper.prototype.export_for_printing.apply(this, arguments);
            res.sale_online = this.get_sale_online();
            res.note = this.get_note();
            // SangNt comment: remove sale online note for receipt printing
            // res.note_sale_online = this.get_note_sale_online();
            return res;
        },
        set_sale_online: function (sale_online) {
            this.sale_online = sale_online;
        },
        get_sale_online: function () {
            return this.sale_online;
        },

        get_note: function () {
            return this.note;
        },
        set_note: function (note) {
            this.note = note;
        },
        get_note_sale_online: function () {
            return this.note_sale_online;
        },
        set_note_sale_online: function (note_sale_online) {
            this.note_sale_online = note_sale_online;
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
                x_source_order_id: get_attr(message, "source_order_id")
            });

            console.log(message);

            if (new_order) {
                console.log(new_order);
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
                // var products_info = [];
                var arr_product_combo_info = []
                orderLines.forEach(function (line) {
                    if (!line.sale_online_id) {
                        let product = self.db.get_product_by_id(line.product_id)
                        //lưu các line là chi tiết combo các sản phẩm
                        arr_product_combo_info.push(line)
                        // products_info.push({
                        //     "product": {
                        //         'display_name': product.display_name,
                        //         'id': product.id,
                        //     },
                        //     'qty': line.quantity,
                        //     'price': product.lst_price,
                        //     'id': line.product_id,
                        // });
                    } else {
                        var product = self.db.get_product_by_id(line.product_id);
                        // if(product.sale_ok == false){
                        //      this.showPopup('ErrorPopup', {
                        //         title: this.env._t('Thông báo'),
                        //         body: this.env._t('Trong đơn hàng có sản phẩm không được phép bán. ' + product.display_name),
                        //     });
                        //     return false;
                        // }
                        if (typeof product == 'undefined') {
                            // Gui.showPopup('ErrorPopup', {
                            //     title: _t('Thông báo'),
                            //     body: _t('Trong đơn hàng có sản phẩm không được phép bán.'),
                            // });
                            // return false;
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
                // console.log('new_order.orderlines.models', new_order.orderlines.models)
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
                    // if (model.x_is_combo) {
                    //     model.set_combo_prod_info(products_info);
                    // }
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