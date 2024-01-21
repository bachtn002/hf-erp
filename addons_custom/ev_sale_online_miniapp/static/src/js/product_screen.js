odoo.define('ev_sale_online_miniapp.ProductScreen', function (require) {
    'use strict'

    const ProductScreen = require('ev_pos_ConfirmPaymentPopup_custom.ProductScreenCustom')
    const Registries = require('point_of_sale.Registries')
    var core = require('web.core')
    var _t = core._t

    let ButtonPay = ProductScreen => class extends ProductScreen {
        async _onClickPay() {
            let current_order = this.env.pos.get_order()
            if (current_order.get_client()){
                if (current_order.get_client().loyalty_points < current_order.get_spent_points()){
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Thông báo'), body: this.env._t('Không thể sử dụng điểm nhỏ hơn điểm tích lũy!'),
                    });
                    return
                }
            }
            return current_order.sale_online ? (() => {
                current_order.get_paymentlines().forEach((item)=>{
                    current_order.remove_paymentline(item)
                })

                let select_channel_value = document.getElementById('select-channel').value
                current_order.x_id_pos_channel = select_channel_value
                let pay_methods = this.env.pos.payment_methods
                this.env.pos.list_payment_methods_by_channel = []
                for (let i = 0; i < pay_methods.length; i++) {
                    if (pay_methods[i]['pos_channel_ids'].includes(parseInt(select_channel_value)) === true) {
                        this.env.pos.list_payment_methods_by_channel.push(pay_methods[i])
                    }
                }
                let pay_sale_online_ids = []
                let total_amount_payment = 0
                current_order.payment_info_sale_online.forEach((item) => {
                    pay_sale_online_ids.push(item[0])
                    total_amount_payment = parseFloat(item[1])
                })

                pay_methods.forEach((item) => {
                    pay_sale_online_ids.includes(item['id']) ? current_order.add_paymentline(item) : null
                })

                let channel_current = self.posmodel.list_pos_channel_online.filter((i) => {
                    return (i.id === this.env.pos.get_order().x_id_pos_channel_sale_online)
                })
                current_order.check_is_not_allow_editing = channel_current[0]['is_not_allow_editing']
                if (current_order.check_is_not_allow_editing) {
                    this.showScreen('PaymentScreen')
                    this.allocate_total()
                } else {
                    this.allocate_total()
                    super._onClickPay()
                }
            })() : super._onClickPay()
        }
    }

    Registries.Component.extend(ProductScreen, ButtonPay)
    return ProductScreen
})