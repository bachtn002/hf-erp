odoo.define('ev_sale_online_miniapp.NumberBufferSaleOnline', function (require) {
    'use strict'

    const NumberBuffer = require('point_of_sale.NumberBuffer')

    NumberBuffer._onNonKeyboardInput = function (event) {
        return this.component ? (() => {
            let channel_current = self.posmodel.list_pos_channel_online.filter((i) => {
                return (i.id === this.component.env.pos.get_order().x_id_pos_channel_sale_online)
            })
            let is_not_allow_editing = false
            if (channel_current.length > 0) {
                is_not_allow_editing = channel_current[0]['is_not_allow_editing']
            }

            return this.component.env.pos.get_order().sale_online ? (() => {
                if (this.component.env.pos.get_order().is_created_by_api || is_not_allow_editing) {
                    let pay_sale_online_ids = []
                    this.component.env.pos.get_order().payment_info_sale_online.forEach((item) => {
                        pay_sale_online_ids.push(item[0])
                    })
                    if (this.component.env.pos.get_order().selected_paymentline) {
                        pay_sale_online_ids.includes(this.component.env.pos.get_order().selected_paymentline.payment_method.id) ? null : this._bufferEvents(this._onInput(event => event.detail.key))(event)
                    }
                } else {
                    this._bufferEvents(this._onInput(event => event.detail.key))(event)
                }
            })() : this._bufferEvents(this._onInput(event => event.detail.key))(event)
        })() : null
    }

    NumberBuffer._onKeyboardInput = function (event) {
        return this.component ? (() => {
            let channel_current = self.posmodel.list_pos_channel_online.filter((i) => {
                return (i.id === this.component.env.pos.get_order().x_id_pos_channel_sale_online)
            })
            let is_not_allow_editing = false
            if (channel_current.length > 0) {
                is_not_allow_editing = channel_current[0]['is_not_allow_editing']
            }
            // trường hợp đang gọi thanh toán QR thì k cho phép nhập bàn phím
            if (this.component.env.pos.get_order().is_calling_qrcode_payment){
                return null
            }

            return this.component.env.pos.get_order().sale_online ? (() => {
                if (this.component.env.pos.get_order().is_created_by_api || is_not_allow_editing) {
                    let pay_sale_online_ids = []
                    this.component.env.pos.get_order().payment_info_sale_online.forEach((item) => {
                        pay_sale_online_ids.push(item[0])
                    })
                    // FIXME không thêm được phương thức đã thanh toán trên đơn online đối với đơn k sửa
                    if (this.component.env.pos.get_order().selected_paymentline) {
                        pay_sale_online_ids.includes(this.component.env.pos.get_order().selected_paymentline.payment_method.id) ? null : this._bufferEvents(this._onInput(event => event.key))(event)
                    }
                } else {
                    this._bufferEvents(this._onInput(event => event.key))(event)
                }
            })() : this._bufferEvents(this._onInput(event => event.key))(event)

        })() : null
    }
    return NumberBuffer
})