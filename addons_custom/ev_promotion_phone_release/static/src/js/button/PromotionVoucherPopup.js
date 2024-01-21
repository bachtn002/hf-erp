odoo.define('ev_promotion_phone_release.VoucherPromotionPopup', function (require) {
    'use strict';

    const VoucherPromotionPopup = require('ev_pos_voucher_ui.VoucherPromotionPopup')
    const Registries = require('point_of_sale.Registries');

    let VoucherPromotionPhonePopup = VoucherPromotionPopup =>
        class extends VoucherPromotionPopup {
            constructor() {
                super(...arguments);
            }

            async onClickApplyPromotionCode(ev) {
                let payload = this.getPayload()
                var customerID = false;
                const order = this.props.order;
                if (order.get_client()) {
                    customerID = order.get_client().id;
                }
                this.state.message = undefined;
                if (payload['newArray'].length > 0) {
                    let name = payload['newArray'][0]['text']
                    var ifConnected = window.navigator.onLine;
                    if (!ifConnected) {
                        this.state.message = '* Đường truyền mạng có vấn đề. Vui lòng kiểm tra lại!';
                        this.playSound('error');
                    }
                    let args_code = [order.name, order.name, name, customerID];
                    const result = await this.rpc({
                        model: 'promotion.voucher.count',
                        method: 'check_promotion_code',
                        args: args_code,
                    }).then((response) => {
                        if ('message' in response) {
                            // message = response['message'];
                            this.state.message = '* ' + response['message'];
                            this.playSound('error');
                        }
                    });

                } else {
                    this.state.message = '* Xin vui lòng nhập mã khuyến mại!'
                    this.playSound('error');
                }
                // Sau khi check các trường hợp không hợp lệ thực hiện tiếp
                if (this.state.message === undefined) {
                    await this.confirm()
                }

                ev.preventDefault();
                this.props.onClickApplyPromotionCodeCha(ev, 'ABC');
                // this.cancel();
            }

            async confirm() {
                await this.check_promotion()
                this.props.resolve({
                    confirmed: true,
                    payload: await this.getPayload(),
                    check_promotion: this.state.promotion_id,
                    get_promotion_id: this.state.get_promotion_id,
                    code_promotion: this.state.code_promotion,
                });
                this.trigger('close-popup');
            }

            async check_promotion() {
            let payload = this.getPayload()
            var customerID = false;
            const order = this.props.order;
            if (order.get_client()) {
                customerID = order.get_client().id;
            }
            this.state.promotion_id = false
            if (payload['newArray'].length > 0) {
                let id = payload['newArray'][0]['_id']
                let name = payload['newArray'][0]['text']
                let args = [id, name, customerID];
                var ifConnected = window.navigator.onLine;
                if (!ifConnected) {
                    this.state.message = '* Đường truyền mạng có vấn đề. Vui lòng kiểm tra lại!';
                    this.playSound('error');
                }
                const result = await this.rpc({
                    model: 'promotion.voucher.line',
                    method: 'check_promotion',
                    args: args,
                }).then((response) => {
                    if ('promotion_id' in response) {
                        this.state.promotion_id = response['promotion_id']
                    }
                    if ('get_promotion_id' in response) {
                        this.state.get_promotion_id = response['get_promotion_id']
                    }
                    if ('code_promotion' in response) {
                        this.state.code_promotion = response['code_promotion']
                    }
                });
            }
            return this.state
        }
        }


    Registries.Component.extend(VoucherPromotionPopup, VoucherPromotionPhonePopup);

    return VoucherPromotionPopup;

})