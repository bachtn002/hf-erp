odoo.define('ev_sale_online_miniapp.PaymentScreenButtonDeletePayment', function (require) {
    'use strict'

    const PaymentScreen = require('ev_pos_voucher_ui.PaymentScreen')
    const Registries = require('point_of_sale.Registries')


    let ButtonDeletePayment = PaymentScreen => class extends PaymentScreen {
        deletePaymentLine(event) {
            let channel_current = self.posmodel.list_pos_channel_online.filter((i) => {
                return (i.id === this.env.pos.get_order().x_id_pos_channel_sale_online)
            })
            let is_not_allow_editing = false
            if (channel_current.length > 0) {
                is_not_allow_editing = channel_current[0]['is_not_allow_editing']
            }

            return this.env.pos.get_order().sale_online ? (() => {
                if (this.env.pos.get_order().is_created_by_api || is_not_allow_editing) {
                    let pay_sale_online_ids = []
                    this.env.pos.get_order().payment_info_sale_online.forEach((item) => {
                        pay_sale_online_ids.push(item[0])
                    })
                    const {cid} = event.detail
                    const line = this.paymentLines.find((line) => line.cid === cid)
                    if (line) {
                        if (pay_sale_online_ids.includes(line.payment_method.id)) {
                            return
                        } else {
                            super.deletePaymentLine(event)
                        }
                    }
                } else {
                    super.deletePaymentLine(event)
                }
            })() : super.deletePaymentLine(event)
        }

        async addNewPaymentLine({detail: paymentMethod}) {

            const inputVatNumber = document.getElementById('x_sinvoice_vat')
            const inputCom = document.getElementById('x_sinvoice_company_name')
            const inputAdd = document.getElementById('x_sinvoice_address')
            const inputMail = document.getElementById('x_sinvoice_email')

            inputVatNumber.value ? this.env.pos.get_order().x_sinvoice_vat = inputVatNumber.value : null
            inputCom.value ? this.env.pos.get_order().x_sinvoice_company_name = inputCom.value : null
            inputAdd.value ? this.env.pos.get_order().x_sinvoice_address = inputAdd.value : null
            inputMail.value ? this.env.pos.get_order().x_sinvoice_email = inputMail.value : null


            let channel_current = self.posmodel.list_pos_channel_online.filter((i) => {
                return (i.id === this.env.pos.get_order().x_id_pos_channel_sale_online)
            })
            let is_not_allow_editing = false
            if (channel_current.length > 0) {
                is_not_allow_editing = channel_current[0]['is_not_allow_editing']
            }

            return this.env.pos.get_order().sale_online ? (() => {
                if (this.env.pos.get_order().is_created_by_api || is_not_allow_editing) {
                    let pay_sale_online_ids = []
                    this.env.pos.get_order().payment_info_sale_online.forEach((item) => {
                        pay_sale_online_ids.push(item[0])
                    })
                    pay_sale_online_ids.includes(paymentMethod['id']) ? null : super.addNewPaymentLine({detail: paymentMethod})
                } else {
                    super.addNewPaymentLine({detail: paymentMethod})
                }
            })() : super.addNewPaymentLine({detail: paymentMethod})
        }
    }

    Registries.Component.extend(PaymentScreen, ButtonDeletePayment)
    return PaymentScreen

})