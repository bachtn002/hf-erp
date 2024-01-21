odoo.define('ev_pos_loyalty_channel.Order', function (require) {
    "use strict"

    const pos_custom = require('ev_pos_loyalty_custom.Order');

    let _superOrder = pos_custom.Order;
    pos_custom.Order = pos_custom.Order.extend({
        get_won_points: function () {
            let order = this.pos.get_order();
            let self = this;
            let channel_ids = this.pos.loyalty.x_pos_channel_ids;
            let select_channel = document.getElementById('select-channel')
            let select_channel_value;
            if (select_channel !== null) {
                select_channel_value = parseInt(select_channel.value);
            } else if (order.x_id_pos_channel !== '') {
                select_channel_value = parseInt(this.pos.get_order().x_id_pos_channel);
            } else if (order.x_id_pos_channel_sale_online !== '') {
                select_channel_value = parseInt(this.pos.get_order().x_id_pos_channel_sale_online);
            } else {
                select_channel_value = order.x_select_channel_value;
            }
            if (channel_ids.length === 0 || !channel_ids.includes(select_channel_value)) {
                let orderLinesToRemove = [];
                for (var orderLine of order.orderlines.models){
                    if (orderLine.reward_custom_id === 'reward') {
                         orderLinesToRemove.push(orderLine);
                    }
                }
                for (var orderLine of orderLinesToRemove) {
                    order.orderlines.remove(orderLine);
                }
                return 0;
            } else {
                return _superOrder.prototype.get_won_points.call(this);
            }
        },

    });

    return pos_custom;
});
