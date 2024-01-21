odoo.define('ev_payment_qrcode.NumpadInputKeyboard', function (require) {
    'use strict'

    const NumberBuffer = require('ev_sale_online_miniapp.NumberBufferSaleOnline')

    NumberBuffer._onKeyboardInput = function (event) {
        return this.component ? (() => {
            return this.component.env.pos.get_order().is_block_numpad_input_keyboard ? (() => {
                return null
            })() : this._bufferEvents(this._onInput(event => event.key))(event)
        })() : null
    }

    return NumberBuffer
})