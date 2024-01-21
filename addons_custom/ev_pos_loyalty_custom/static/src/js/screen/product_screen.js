odoo.define('ev_pos_loyalty_custom.ProductScreen', function (require) {
    "use strict"

    const core = require('web.core');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const {useListener} = require('web.custom_hooks');
    const {debounce} = owl.utils;
    const {useState} = owl.hooks;
    const _t = core._t;

    const rpc = require('web.rpc');
    let PosLoyaltyCustomProductScreen = ProductScreen =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                // useListener('search_customer', () => this.search_customer(event));
            }

            // async search_customer(event) {
            // }

            async _onClickCustomer() {
                console.log('check 2')
                // super._onClickCustomer();
                // IMPROVEMENT: This code snippet is very similar to selectClient of PaymentScreen.
                const currentClient = this.currentOrder.get_client();
                const {confirmed, payload: newClient} = await this.showTempScreen(
                    'ClientListScreen',
                    {client: currentClient}
                );
                if (confirmed) {
                    const order_before = this.currentOrder;
                    var promotion_code;
                    var promotion_id;
                    order_before.orderlines.forEach((line) => {
                        if (line.promotion_code && line.promotion_id) {
                            promotion_code = line.promotion_code;
                            promotion_id = line.promotion_id;
                        }
                    });
                    // cập nhật trạng thái promotion code khi bấm button khách hàng
                    var promotion_code = []
                    var promotion_id = []
                    const order_count = this.currentOrder;
                    order_before.orderlines.forEach((line) => {
                        if (line.promotion_code && line.promotion_id) {
                            // promotion_code = line.promotion_code;
                            promotion_code.push(line.promotion_code)
                            promotion_id.push(line.promotion_id)
                            let args_code = [order_count.name, order_count.name, promotion_code[0]];
                            this.rpc({
                                model: 'promotion.voucher.count',
                                method: 'delete_promotion_code_used',
                                args: args_code,
                            });
                        }
                    });
                    this.env.pos.removePromotionsApplied();
                    this.generatePromotions();
                    const order = this.currentOrder;
                    let args = [promotion_id, promotion_code];
                    // this.rpc({
                    //     model: 'promotion.voucher.line',
                    //     method: 'update_promotion_used_return',
                    //     args: args,
                    // });
                    const current_order = this.env.pos.get_order()
                    const orderlines = this.currentOrder.orderlines;
                    current_order.orderlines.forEach((line) => {
                        if (line.promotion_code !== 'undefined' && line.price < 0) {
                            current_order.remove_orderline(line);
                        }
                        if (line.promotion_id !== 'undefined' && line.price < 0) {
                            current_order.remove_orderline(line);
                        }
                        if (line.reward_custom_id === 'reward') {
                            current_order.remove_orderline(line);
                        }
                    });
                    this.currentOrder.set_client(newClient);
                    this.currentOrder.updatePricelist(newClient);
                    this.env.pos.removePromotionsApplied();
                    this.generatePromotions();
                }
            }
        };
    Registries.Component.extend(ProductScreen, PosLoyaltyCustomProductScreen);

    return ProductScreen;
});