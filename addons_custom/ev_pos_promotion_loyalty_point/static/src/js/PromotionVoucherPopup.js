odoo.define('ev_promotion_loyalty_point.VoucherPromotionPopup', function (require) {
    'use strict';

    const VoucherPromotionPopup = require('ev_promotion_phone_release.VoucherPromotionPopup')
    const Registries = require('point_of_sale.Registries');

    let VoucherPromotionPhonePopup = VoucherPromotionPopup =>
        class extends VoucherPromotionPopup {
            constructor() {
                super(...arguments);
            }

        async onClickApplyPromotionCode(ev) {
                let payload = this.getPayload()
                const order = this.props.order;
                if (this.props.isVerifyBarcode === true) {
                    this.state.message = undefined;
                    var call_api = false;
                    if (payload['newArray'].length > 0) {
                        let name = payload['newArray'][0]['text']
                        var ifConnected = window.navigator.onLine;
                        if (!ifConnected) {
                            this.state.message = '* Đường truyền mạng có vấn đề. Vui lòng kiểm tra lại!';
                            this.playSound('error');
                        }
                        let check = null
                        let args_code = [name, name];
                        if (!this.el.getElementsByClassName('button confirm').disabled && !call_api){
                            this.el.getElementsByClassName('button confirm').disabled = true;
                            call_api = true;
                            const result = await this.rpc({
                                model: 'pos.promotion.loyalty.point',
                                method: 'check_partner',
                                args: args_code,
                            }).then((response) => {
                                if (!response) {
                                    this.state.message = '* Mã thành viên không hợp lệ!'
                                    this.playSound('error');
                                    this.el.getElementsByClassName('button confirm').disabled = false;
                                } else {
                                    check = response.toString()
                                }
                            });
                            var partner = posmodel.db.search_partner(check)
                            if (partner.length > 0){
                                order.set_client(partner[0]);
                                order.set_x_is_miniapp_member(true);
                                order.set_x_note_member_app(name)
                            }
                            else {
                                check !== null ? await this.env.pos.search_partner_to_phone(check) : null
                                console.log(check)
                                let partner_partner = self.posmodel.db.search_partner(check)
                                console.log(partner_partner)
                                if (partner_partner && partner_partner.length > 0) {
                                    order.set_client(partner_partner[0])
                                    order.set_x_is_miniapp_member(true)
                                    order.set_x_note_member_app(name)
                                }
                            }
                        }

                    } else {
                        this.state.message = '* Xin vui lòng nhập mã thành viên!'
                        this.playSound('error');
                         this.el.getElementsByClassName('button confirm').disabled = false;
                    }
                    // Sau khi check các trường hợp không hợp lệ thực hiện tiếp
                    if (this.state.message === undefined && call_api) {
                        this.props.resolve({confirmed: true});
                        this.trigger('close-popup');
                    }
                    ev.preventDefault();
                } else {
                    await super.onClickApplyPromotionCode(ev);
                }
            }

        }

    Registries.Component.extend(VoucherPromotionPopup, VoucherPromotionPhonePopup);

    return VoucherPromotionPopup;

})