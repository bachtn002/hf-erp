odoo.define('ev_pos_channel.ActionpadWidget', function (require) {
    'use strict'
    const PosComponent = require('point_of_sale.PosComponent')
    const Registries = require('point_of_sale.Registries')
    const ActionpadWidget = require('point_of_sale.ActionpadWidget')

    let ChannelActionpadWidget = ActionpadWidget => class extends ActionpadWidget {
        returnPickSelectedChannel() {
            var x_is_selecting = this.env.pos.get_order().x_select_channel_value
            var x_id_pos_channel_sale_online = this.env.pos.get_order().x_id_pos_channel_sale_online
            if (x_id_pos_channel_sale_online !== 0) {
                return [this.env.pos.list_pos_channel_online, -1, x_id_pos_channel_sale_online]
            }
            if (x_is_selecting !== 0) return [this.env.pos.list_pos_channel_no_online_channel, x_is_selecting]
            return [this.env.pos.list_pos_channel_no_online_channel, 0]
        }

        clickSelectChannel() {
            let element = document.getElementById('select-channel')
            if (element) {
                let promotions_all = self.posmodel.getValidPromotions(null, true)
                let promotions = []
                promotions_all.forEach((pro) => {
                    if (!pro.check_promotion) {
                        promotions.push(pro)
                    }
                })
                let appliedPromotions = self.posmodel.getPromotionsApplied();
                let appliedProIds = appliedPromotions.map((item) => {
                    return item.id
                });
                promotions.forEach((item) => {
                    let select = _.indexOf(appliedProIds, item.id) != -1
                    item.setSelect(select)
                })
                let control_button_number = document.getElementsByClassName('control-button-number')
                if (control_button_number) {
                    control_button_number[0].innerHTML = promotions.length
                }
            }
        }

    }

    Registries.Component.extend(ActionpadWidget, ChannelActionpadWidget)
    return ActionpadWidget
})