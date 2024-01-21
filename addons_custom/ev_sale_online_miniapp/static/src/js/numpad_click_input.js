odoo.define('ev_sale_online_miniapp.Numpad', function (require) {
    'use strict'
    const Numpad = require('point_of_sale.NumpadWidget')
    const Registries = require('point_of_sale.Registries')


    let InputNumpad = Numpad => class extends Numpad {
        sendInput(key) {
            let channel_current = self.posmodel.list_pos_channel_online.filter((i) => {
                return (i.id === this.env.pos.get_order().x_id_pos_channel_sale_online)
            })
            let is_not_allow_editing = false
            if (channel_current.length > 0) {
                is_not_allow_editing = channel_current[0]['is_not_allow_editing']
            }

            return this.env.pos.get_order().sale_online ? (() => {
                if (this.env.pos.get_order().is_created_by_api) {
                    return
                } else if (is_not_allow_editing) {
                    return
                } else {
                    super.sendInput(key)
                }
            })() : super.sendInput(key)
        }
    }

    Registries.Component.extend(Numpad, InputNumpad)
    return Numpad
})