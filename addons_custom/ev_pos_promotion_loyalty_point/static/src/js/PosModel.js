odoo.define('ev_pos_promotion_loyalty_point.PosModel', function (require) {
    'use strict'

    const models = require('ev_pos_channel.ChannelPosModel')
    let PosModel = models.PosModel;
    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = PosModel.extend({

        /**
         * applyPromotions
         *
         * Áp dụng danh sách promotion vào đơn hàng
         *
         * @param {} promotions
         * @param {} order
         */
        applyPromotions: async function (promotions, order = null) {
            order = order || this.get_order();
            let ordersAppliedPromotions = this.getOrderAppliedPromotions();
            if (!ordersAppliedPromotions.hasOwnProperty(order.uid)) {
                ordersAppliedPromotions[order.uid] = [];
            }
            let data = ordersAppliedPromotions[order.uid].concat(promotions);
            let duplicateIds = [];
            data = data.filter((item) => {
                return _.indexOf(duplicateIds, item.id) === -1;
            });

            // Xắp xếp lại promotion theo thứ tự
            ordersAppliedPromotions[order.uid] = this.sortPromotions(data);

            // Đặt CTKM KHTT ở cuối
            let promotion_loyalty_point = data.filter(item => item.type === 'loyalty_point');
            let otherItems = data.filter(item => item.type !== 'loyalty_point');

            data = otherItems.concat(promotion_loyalty_point);

            // Lưu list promotion áp dụng cho đơn hàng
            // Và áp dụng theo trình tự đã sắp xếp
            this.saveOrderAppliedPromotions(ordersAppliedPromotions);
            data.forEach((item) => {
                item.applyPromotionToOrder(order);
            });
            // Bỏ giảm trừ điểm tích lũy sau khi áp dụng promotion đối với ctkm không phải là
            var promotion_not_loyalty_point = promotions.filter((item) => {
                return item.type !== 'loyalty_point';
            });
            if (promotion_not_loyalty_point.length > 0) {
                order.orderlines.forEach((line) => {
                    if (line) {
                        if (line.reward_custom_id === 'reward') {
                            order.remove_orderline(line);
                        }
                    }
                });
            }
        },

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
            order.set_x_promotion_loyalty_point(0)
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