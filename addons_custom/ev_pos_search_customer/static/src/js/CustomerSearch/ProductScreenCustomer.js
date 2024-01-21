odoo.define('ev_pos_search_customer.ProductScreenCustomer', function (require) {
    "use strict"

    const PosComponent = require('point_of_sale.PosComponent');
    const ClientListScreen = require('point_of_sale.ClientListScreen');
    const Registries = require('point_of_sale.Registries');
    const {useListener} = require('web.custom_hooks');
    const {debounce} = owl.utils;
    const core = require('web.core');
    const _t = core._t;

    class ProductScreenCustomer extends ClientListScreen {
        constructor() {
            super(...arguments);
            useListener('create_customer', () => this._create_customer());
            this.handleOnClickSearchCustomer = this.handleOnClickSearchCustomer.bind(this);
            this.check_sent = false;
        }

        handleOnClickSearchCustomer(event, promotions) {
            this.props.onClickSearchCustomerParent(event, promotions);
        }

        get nextButton() {
            if (!this.props.client) {
                // return {command: 'set', text: 'Set Customer'};
                return {command: 'set', text: _t('Promotions')};

            } else if (this.props.client && this.props.client === this.state.selectedClient) {
                return {command: 'deselect', text: 'Deselect Customer'};
            } else {
                return {command: 'set', text: 'Change Customer'};
            }
        }

        get clients() {
            if (this.state.query && this.state.query.trim() !== '') {
                return this.env.pos.db.search_partner_limit(this.state.query.trim());
            }
        }

        async _create_customer() {
            const currentClient = this.env.pos.get_order().get_client();
            const {confirmed, payload: newClient} = await this.showTempScreen(
                'ClientListScreen',
                {client: currentClient, isEditMode: true, detailIsShown: true, isNewClient: true}
            );
            if (confirmed) {
                this.env.pos.get_order().set_client(newClient);
                this.env.pos.get_order().updatePricelist(newClient);
            }
        }

        async updateClientList(event) {
            this.state.query = event.target.value.split('-')[0];

            if (event.target.value.length >= this.env.pos.config.x_number_search_limit) {
                const clients = this.clients;
                const order_before = this.currentOrder;
                var promotion_code = []
                var promotion_id = []
                if (typeof clients == 'undefined') {
                    let order = this.env.pos.get_order();
                    order.set_client(false);
                    return;
                }
                if (clients.length === 1 && !event.composed) {
                    let order = this.env.pos.get_order();
                    order_before.orderlines.forEach((line) => {
                        if (line.promotion_code && line.promotion_id) {
                            // promotion_code = line.promotion_code;
                            promotion_code.push(line.promotion_code)
                            promotion_id.push(line.promotion_id)
                            // promotion_code.forEach((code) => {
                            //     let args_code = [order.name, order.name, code];
                            //     this.rpc({
                            //         model: 'promotion.voucher.count',
                            //         method: 'delete_promotion_code_used',
                            //         args: args_code,
                            //     });
                            // })
                        }
                    });
                    order.set_client(clients[0]);
                    this.props.upDatePromotion(event);
                }

                if (event.code === 'Enter' && clients.length === 1) {
                    let order = this.env.pos.get_order();
                    order.set_client(clients[0]);
                    this.state.selectedClient = clients[0];
                    event.target.value = "";
                    order_before.orderlines.forEach((line) => {
                        if (line.promotion_code && line.promotion_id) {
                            // promotion_code = line.promotion_code;
                            promotion_code.push(line.promotion_code)
                            promotion_id.push(line.promotion_id)
                            // promotion_code.forEach((code) => {
                            //     let args_code = [order.name, order.name, code];
                            //     this.rpc({
                            //         model: 'promotion.voucher.count',
                            //         method: 'delete_promotion_code_used',
                            //         args: args_code,
                            //     });
                            // })
                        }
                    });
                    this.props.upDatePromotion(event);
                }

                if (event.code === undefined && clients.length === 1) {
                    let order = this.env.pos.get_order();
                    order.set_client(clients[0]);
                    this.state.selectedClient = clients[0];
                    event.target.value = "";
                }
                var check_enter = false;
                if (event.code === 'Enter' || event.code === 'NumpadEnter'){
                    check_enter = true;
                }
                if (clients.length === 0 && check_enter) {
                    let order = this.env.pos.get_order();
                    order.set_client(false);
                    if(this.check_sent == false){
                        try {
                            let search_string = event.target.value;
                            this.check_sent = true;
                            var search_phone = await this.env.pos.search_partner_to_phone(search_string);
                            this.check_sent = false;
                            this.render();
                        } catch (error) {
                            this.check_sent = false;
                            if (error == undefined) {
                                await this.showPopup('OfflineErrorPopup', {
                                    title: this.env._t('Offline'),
                                    body: this.env._t('Unable to search customer.'),
                                });
                            }
                        }
                    }
                }
                else {
                    this.render();
                    // let order = this.env.pos.get_order();
                    // order_before.orderlines.forEach((line) => {
                    //     if (line.promotion_code && line.promotion_id) {
                    //         // promotion_code = line.promotion_code;
                    //         promotion_code.push(line.promotion_code)
                    //         promotion_id.push(line.promotion_id)
                    //         promotion_code.forEach((code) => {
                    //             let args_code = [order.name, order.name, code];
                    //             this.rpc({
                    //                 model: 'promotion.voucher.count',
                    //                 method: 'delete_promotion_code_used',
                    //                 args: args_code,
                    //             });
                    //         })
                    //     }
                    // });
                    // this.props.upDatePromotion(event);
                }
            }
        }
    }

    ProductScreenCustomer.template = 'ProductScreenCustomer';

    Registries.Component.add(ProductScreenCustomer);

    return ProductScreenCustomer

});