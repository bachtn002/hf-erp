odoo.define('ev_pos_online.pos_online', function (require) {
    "use strict";

    const models = require('point_of_sale.models');
    const ClientListScreen = require('point_of_sale.ClientListScreen');
    const Registries = require('point_of_sale.Registries');

    var exports = {};
    models.load_fields('pos.config', 'x_limit_partner', 'x_number_search_limit', 'x_apply_fix_customer');

    let PosModel = models.PosModel;
    models.PosModel = PosModel.extend({
        initialize: function (session, attributes) {
            var self = this;
            PosModel.prototype.initialize.call(this, session, attributes);
            this.session.user_context.limit_partner = 20;
            this.session.user_context.limit_product = 20;
            this.session.user_context.display_default_code = false;
        },

        load_orders: function () {
            var jsons = this.db.get_unpaid_orders();
            for (var i = 0; i < jsons.length; i++) {
                jsons[i].lines.forEach((line) => {
                    // trường hợp promotion code đã áp dụng, load lại POS thì cập nhật lại trạng thái promotion code
                    var promotion_code = []
                    var promotion_id = []
                    if (line[2].promotion_code && line[2].promotion_id) {
                        promotion_code.push(line[2].promotion_code)
                        promotion_id.push(line[2].promotion_id)
                        // load lại pos không cập nhật promotion code
                        // promotion_code.forEach((code) => {
                        //     let args_code = [jsons[i].name, jsons[i].name, code];
                        //     this.rpc({
                        //         model: 'promotion.voucher.count',
                        //         method: 'delete_promotion_code_used',
                        //         args: args_code,
                        //     });
                        // })
                    }
                })
                jsons[i].statement_ids.forEach((line) => {
                    var promotion_voucher = []
                    if (line[2].lot_name) {
                        promotion_voucher.push(line[2].lot_name)
                        let args_code = [jsons[i].name, promotion_voucher[0]];
                        this.rpc({
                            model: 'stock.production.lot',
                            method: 'update_voucher_status_after_delete',
                            args: args_code,
                        })
                    }
                })
                this.db.remove_unpaid_order(jsons[i]);
            }
            PosModel.prototype.load_orders.apply(this, arguments);
        },

        prepare_phone_partners_domain: function (phone) {
            return [['phone', 'ilike', phone]];
        },

        prepare_id_partners_domain: function (id) {
            return [['id', '=', id]];
        },

        search_partner_to_phone: function (phone) {
            var self = this;
            return new Promise(function (resolve, reject) {
                var fields = _.find(self.models, function (model) {
                    return model.label === 'load_partners';
                }).fields;
                var domain = self.prepare_phone_partners_domain(phone);
                self.rpc({
                    model: 'res.partner',
                    method: 'search_partner_by_phone',
                    args: [phone, fields, 0, 1],
                }, {
                    timeout: 10000,
                    shadow: true,
                })
                    .then(function (partners) {
                        console.log('partners', partners)
                        if (self.db.add_partners(partners)) {   // check if the partners we got were real updates
                            resolve();
                        } else {
                            reject('Customer does not exist!');
                        }
                    }, function (type, err) {
                        reject();
                    });
            });
        },


        search_partner_to_id: function (id) {
            var self = this;
            return new Promise(function (resolve, reject) {
                var fields = _.find(self.models, function (model) {
                    return model.label === 'load_partners';
                }).fields;
                var domain = self.prepare_id_partners_domain(id);
                self.rpc({
                    model: 'res.partner',
                    method: 'search_partner_by_id',
                    args: [id, fields, 0, 1],
                }, {
                    timeout: 10000,
                    shadow: true,
                })
                    .then(function (partners) {
                        if (self.db.add_partners(partners)) {   // check if the partners we got were real updates
                            resolve();
                        } else {
                            reject('Customer does not exist!');
                        }
                    }, function (type, err) {
                        reject();
                    });
            });
        },

        prepare_name_product_domain: function (search_key, load_data) {
            return ['&', '&', ['sale_ok', '=', true], ['available_in_pos', '=', true], '|', '|', ['default_code', 'ilike', search_key], ['barcode', 'ilike', search_key], ['name', 'ilike', search_key]]
        },

        search_product_to_server: function (search_key) {
            var self = this;
            return new Promise(function (resolve, reject) {
                var fields = _.find(self.models, function (model) {
                    return model.model === 'product.product';
                }).fields;
                var domain = self.prepare_name_product_domain(search_key);
                self.rpc({
                    model: 'product.product',
                    method: 'search_read',
                    args: [domain, fields, 0, 10],
                }, {
                    timeout: 10000,
                    shadow: true,
                })
                    .then(function (products) {
                        if (products.length > 0) {
                            var using_company_currency = self.config.currency_id[0] === self.company.currency_id[0];
                            var conversion_rate = self.currency.rate / self.company_currency.rate;
                            self.db.add_products(_.map(products, function (product) {
                                if (!using_company_currency) {
                                    product.lst_price = round_pr(product.lst_price * conversion_rate, self.currency.rounding);
                                }
                                product.categ = _.findWhere(self.product_categories, {'id': product.categ_id[0]});
                                product.pos = self;
                                return new models.Product({}, product);
                            }));
                            resolve();
                        } else {
                            reject('Product does not exist!');
                        }
                    }, function (type, err) {
                        reject();
                    });
            });
        },


    });


    let ClientListScreenOnline = ClientListScreen =>
        class extends ClientListScreen {
            constructor() {
                super(...arguments);
                this.state = {
                    query: null,
                    selectedClient: this.props.client,
                    detailIsShown: this.props.detailIsShown || false,
                    isEditMode: this.props.isEditMode || false,
                    isNewClient: this.props.isNewClient || false,
                    editModeProps: {
                        partner: {
                            country_id: this.env.pos.company.country_id,
                            state_id: this.env.pos.company.state_id,
                        }
                    },
                };
                this.check_click = 0;
            }

            async updateClientList(event) {
                super.updateClientList(event);
                const clients = this.clients;
                if (event.type === 'keyup' && clients.length === 0) {
                    try {
                        let search_string = event.target.value;
                        await this.env.pos.search_partner_to_phone(search_string);
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
            }

            async saveChanges(event) {
                this.check_click = this.check_click + 1;
                if(this.check_click > 1){
                    return;
                }
                try {
                    let check_phone = await this.rpc({
                        model: 'res.partner',
                        method: 'check_phone',
                        args: [event.detail.processedChanges],
                    });
                    if (check_phone != true){
                        this.check_click = 0;
                        await this.showPopup('ErrorPopup', {
                             title: this.env._t('Thống báo'),
                             body: check_phone,
                        });
                        return;
                    }

                    let partnerId = await this.rpc({
                        model: 'res.partner',
                        method: 'create_from_ui',
                        args: [event.detail.processedChanges],
                    });
                    await this.env.pos.search_partner_to_id(partnerId);
                    this.state.selectedClient = this.env.pos.db.get_partner_by_id(partnerId);
                    this.state.detailIsShown = false;
                    this.render();
                    this.check_click = 0;
                } catch (error) {
                    this.check_click = 0;
                    if(typeof error != 'object'){
                        await this.showPopup('ErrorPopup', {
                             title: this.env._t('Thống báo'),
                             body: this.env._t('Unable to save changes.'),
                         });
                    } else {
                        if (error.message.code < 0) {
                             await this.showPopup('OfflineErrorPopup', {
                                 title: this.env._t('Offline'),
                                 body: this.env._t('Unable to save changes.'),
                             });
                        } else {
                             throw error;
                        }
                    }

                }
            }


        }

    Registries.Component.extend(ClientListScreen, ClientListScreenOnline);

    return ClientListScreen;

});