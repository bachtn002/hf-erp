odoo.define('ev_sale_online_miniapp.button_validate_order', function (require) {
    'use strict'

    const Registries = require('point_of_sale.Registries')
    const PaymentScreen = require('point_of_sale.PaymentScreen')
    const rpc = require('web.rpc')

    let ButtonValidateOrder = PaymentScreen => class extends PaymentScreen {
        async validateOrder(isForceValidate) {
            let order = this.currentOrder
            let check_sale_online = true
            order.sale_online ? (() => {
                rpc.query({
                    model: 'sale.online',
                    method: 'check_state_sale_online',
                    args: [null, parseInt(order.id_sale_online), order.get_total_with_tax(), order.write_date.toString()]
                })
                    .then((res) => {
                        !res[0] || !res[1] ? (() => {
                            check_sale_online = false
                            this.showPopup('ErrorPopup', {
                                title: this.env._t("Đơn hàng đã thay đổi vui lòng đồng bộ lại."),
                                body: this.env._t(""),
                            })
                            return
                        })() : (() => {
                            if (res[1] && res[0]) {
                                let i = 0
                                order.order_line_info.forEach((item) => {
                                    let line = order.get_orderlines().filter((i) => {
                                        return i['product']['product_tmpl_id'] === item[0]
                                    })
                                    if (line) {
                                        if (line.length > 1) {
                                            line[i].x_is_price_promotion = item[4]
                                            line[i].amount_promotion_loyalty = item[5]
                                            line[i].amount_promotion_total = item[6]
                                            i += 1
                                        } else {
                                            line[0].x_is_price_promotion = item[4]
                                            line[0].amount_promotion_loyalty = item[5]
                                            line[0].amount_promotion_total = item[6]
                                        }
                                    }
                                })
                                super.validateOrder(isForceValidate)
                            } else {
                                super.validateOrder(isForceValidate)
                            }
                        })()
                    })
                    .catch((err) => {
                        console.log(err)
                    })
            })() : super.validateOrder(isForceValidate)
        }
    }

    Registries.Component.extend(PaymentScreen, ButtonValidateOrder)
    return PaymentScreen

})