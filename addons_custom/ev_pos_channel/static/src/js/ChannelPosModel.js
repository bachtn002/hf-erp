odoo.define('ev_pos_channel.ChannelPosModel', function (require) {
    'use strict'

    const models = require('ev_pos_promotion.models')
    let ChannelPosModel = models.PosModel;
    models.PosModel = ChannelPosModel.extend({

        getValidPromotions: function (order = null, show = false) {
            let select_channel = document.getElementById('select-channel')
            order = order || this.get_order()
            if (order.orderlines.length < 1) {
                return []
            }
            let promotions = null
            if (select_channel !== null) {
                promotions = this.getPromotions().filter((item) => {
                    return item.pos_channel_ids.includes(parseInt(select_channel.value))
                })
            } else {
                var select_channel_value = this.env.pos.get_order().x_id_pos_channel
                promotions = this.getPromotions().filter((item) => {
                    return item.pos_channel_ids.includes(parseInt(select_channel_value))
                })
            }
            return promotions.filter((item) => {
                return item.isValidOrder(order, show)
            })
        },
    })

    return models
})