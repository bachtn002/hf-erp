odoo.define('ev_sale_online_miniapp.PosModel', function (require) {
    'use strict'

    const models = require('ev_pos_channel.ChannelPosModel')
    let PosModel = models.PosModel;
    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = PosModel.extend({

         removePromotionsApplied: function (order = null) {
            _super_posmodel.removePromotionsApplied.apply(this, arguments)
            // Bỏ giảm trừ điểm tích lũy
            order = order || this.get_order();
            order.orderlines.forEach((line) => {
                if (line) {
                    if (line.reward_custom_id === 'reward') {
                        order.remove_orderline(line);
                    }
                }
            });
            order.is_applied_promotion = false
            // order.set_x_promotion_loyalty_point(0)
            let rewardLines = order.orderlines.models.filter((line) => {
                return line.price < 0
            })
            rewardLines.forEach((line) => {
                order.remove_orderline(line)
            })
        },

    })

    return models
})