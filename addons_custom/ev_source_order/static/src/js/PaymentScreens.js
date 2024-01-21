odoo.define("ev_source_order.PaymentScreen", function (require) {
    "use strict";

    const core = require('web.core');
    const { Gui } = require('point_of_sale.Gui');
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    var _t = core._t;

    let PaymentScreenSource = PaymentScreen =>
        class extends PaymentScreen {
            async _finalizeValidation() {

                //await this._check_online();
                var self = this;
                var order = this.currentOrder;
                // console.log('check online');
                // console.log(order);
                if (order.sale_online) {
                    order.set_x_source_order_id(order.x_source_order_id);
                }
                // }else {
                //     var x_source_order_id = $('#x_source_order_id').val();
                //     if(x_source_order_id == ""){
                //         Gui.showPopup('ErrorPopup', {
                //             'title': _t('Thông báo'),
                //             'body': _t('Bạn phải chọn nguồn khách hàng để hoàn thành đơn'),
                //         });
                //         return;
                //     }
                //     order.set_x_source_order_id(x_source_order_id);
                // }
                // // console.log(x_source_order_id);
                // // console.log('don hang');
                //console.log(order);
                super._finalizeValidation();
            }
            captureChange(event) {
                this.changes[event.target.name] = event.target.value;
            }

        }

    Registries.Component.extend(PaymentScreen, PaymentScreenSource);
    return PaymentScreen;
});