odoo.define('ev_pos_promotion_gift_code.PaymentScreen', function (require) {
    "use strict"

    const PaymentScreen = require('ev_pos_voucher_ui.PaymentScreen');
    const core = require('web.core');
    const rpc = require('web.rpc');
    const Registries = require('point_of_sale.Registries');

    const _t = core._t;

    let VoucherPaymentScreen = PaymentScreen =>
        class extends PaymentScreen {

            constructor() {
                super(...arguments);
            }

            async validateOrder(isForceValidate) {
                const order = this.currentOrder;
                if (order.x_name_promotion.length > 0 && this.currentOrder.is_paid()){
                    let gift_rules = order.get_rules_valid()
                    if (!gift_rules) return;
                    let data = await this._getData(order, gift_rules)

                    if (data.length > 0) {
                        if (data[0]['promotion_no_code'] !== undefined) {
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('Thông báo'),
                                body: this.env._t('Không tìm thấy mã code có thể áp dụng cho CTKM: ' + data[0]['promotion_no_code'] + '. Vui lòng xóa CTKM để tiếp tục!'),
                            });
                            return;
                        }
                        order.set_code_gave_away(data);
                        order.x_base64_image = data[0][0]['image'];
                    }
                    // else {
                    //     this.showPopup('ErrorPopup', {
                    //         title: this.env._t('Thông báo'),
                    //         body: this.env._t('Không tìm thấy mã code có thể áp dụng cho CTKM: ' + order.x_name_promotion + '. Vui lòng xóa CTKM để tiếp tục!'),
                    //     });
                    //     return;
                    //     }
                    }

                super.validateOrder(isForceValidate);
            }

            async _getData(order, gift_rules) {
                let phone = order.get_client()['phone']
                let args = [gift_rules, phone]
                let res = []
                await rpc.query({
                    model: 'promotion.voucher', method: 'get_promotion_voucher_line', args: args,
                }).then((data) => {
                    if (data['promotion_no_code'] !== undefined) {
                        res.push(data)
                    }
                    if (data.length > 0) {
                        res.push(data)
                    }
                });
                return res;
            }

        };
    Registries.Component.extend(PaymentScreen, VoucherPaymentScreen);

    return PaymentScreen;

});