odoo.define('ev_pos_promotion_loyalty_point.TicketScreen', function (require) {
    'use strict'
    const core = require('web.core')
    const Registries = require('point_of_sale.Registries')
    const TicketScreen = require('ev_sale_online_miniapp.TicketScreen')
    const {useListener} = require('web.custom_hooks')
    const _t = core._t
    const rpc = require('web.rpc')

    let TicketScreenLoyaltyPoint = TicketScreen => class extends TicketScreen {
        constructor() {
            super(...arguments)
        }

        selectOrder(order) {
            if(order.sale_online && order.is_created_by_api){
                order.set_x_is_miniapp_member(true)
            }
            super.selectOrder(order)
            if(order.sale_online && order.is_created_by_api){
                order.set_x_is_miniapp_member(true)
                let listPromotions = this.getValidPromotions(order, order.x_id_pos_channel_sale_online)
                let listPromotionsLoyaltyPoint = listPromotions.filter((item) => {
                    return item.type === 'loyalty_point';
                })
                listPromotionsLoyaltyPoint.forEach((p) => {
                    p.applyPromotionToOrder(order)
                })
            }
        }

    }
    Registries.Component.extend(TicketScreen, TicketScreenLoyaltyPoint)
    return TicketScreen
})