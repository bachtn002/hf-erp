odoo.define('ev_sale_online_miniapp.ListPromotionButton', function (require) {
    'use strict'

    const ListPromotionButton = require('ev_pos_promotion.ListPromotionButton')
    const Registries = require('point_of_sale.Registries')

    let SListPromotionButton = ListPromotionButton => class extends ListPromotionButton {
        onClickListPromotionButton(ev) {
            let channel_current = self.posmodel.list_pos_channel_online.filter((i) => {
                return (i.id === this.env.pos.get_order().x_id_pos_channel_sale_online)
            })
            if (channel_current.length > 0) {
                let is_not_allow_editing = channel_current[0]['is_not_allow_editing']

                return this.env.pos.get_order().sale_online ? (() => {
                    if (this.env.pos.get_order().is_created_by_api) {
                        return
                    } else if (is_not_allow_editing) {
                        return
                    } else {
                        super.onClickListPromotionButton(ev)
                    }
                })() : super.onClickListPromotionButton(ev)
            } else {
                super.onClickListPromotionButton(ev)
            }
        }
    }

    Registries.Component.extend(ListPromotionButton, SListPromotionButton)
    return ListPromotionButton
})