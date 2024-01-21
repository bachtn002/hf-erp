odoo.define("ev_sale_online.TicketScreenCustomDelete", function (require) {
    "use strict";

    const core = require('web.core');
    const Registries = require('point_of_sale.Registries');
    const TicketScreen = require('point_of_sale.TicketScreen');
    const {useListener} = require('web.custom_hooks');
    const {posbus} = require('point_of_sale.utils');

    const _t = core._t;
    const rpc = require('web.rpc');

    let TicketScreenCustomDelete = TicketScreen =>
        class extends TicketScreen {
            constructor() {
                super(...arguments);
            }

            async deleteOrder(order) {
                console.log('test delete')
                const screen = order.get_screen_data();
                if (['ProductScreen', 'PaymentScreen'].includes(screen.name) && order.get_orderlines().length > 0) {
                    const {confirmed} = await this.showPopup('ConfirmPopup', {
                        title: 'Existing orderlines',
                        body: `${order.name} has total amount of ${this.getTotal(
                            order
                        )}, are you sure you want delete this order?`,
                    });
                    if (!confirmed) return;
                }
                if (order) {
                    var promotion_code = []
                    var promotion_id = []
                    order.orderlines.forEach((line) => {
                        if (line.promotion_code && line.promotion_id) {
                            // promotion_code = line.promotion_code;
                            promotion_code.push(line.promotion_code)
                            promotion_id.push(line.promotion_id)
                            promotion_code.forEach((code) => {
                                let args_code = [order.name, order.name, code];
                                this.rpc({
                                    model: 'promotion.voucher.count',
                                    method: 'delete_promotion_code_used',
                                    args: args_code,
                                });
                            })
                        }
                    });
                    order.destroy({reason: 'abandon'});
                }
                posbus.trigger('order-deleted');
            }
        }
    Registries.Component.extend(TicketScreen, TicketScreenCustomDelete);
    return TicketScreen;
});