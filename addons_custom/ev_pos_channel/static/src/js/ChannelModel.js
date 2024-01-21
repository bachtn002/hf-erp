odoo.define('ev_pos_channel.ChannelModel', function (require) {
    'use strict'

    const models = require('point_of_sale.models')
    models.load_models([{
        model: 'pos.channel',
        label: 'Pos Channel',
        fields: ['id', 'code', 'name', 'is_allow_pos', 'is_allow_send_zns', 'is_default_pos', 'is_online_channel', 'is_not_allow_editing'],
        loaded: (self, res) => {
            self.list_pos_channel_online = res
            self.list_pos_channel_no_online_channel = res.filter((item) => {
                return item['is_online_channel'] === false && item['is_allow_pos'] === true
            })
            self.list_payment_methods_by_channel = []
            self.db.addPosChannel(res)
        }
    }])

    models.load_fields('pos.payment.method', ['pos_channel_ids'])
    models.load_fields('pos.promotion', ['pos_channel_ids'])

    let order = models.Order
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            this.x_id_pos_channel = options.x_id_pos_channel || ''                           // Trường này lưu dữ liệu kênh để đẩy xuống backend
            this.x_pos_promotions = options.x_pos_promotions || []
            this.x_select_channel_value = options.x_select_channel_value || 0                // Trường này đánh dấu kênh đang chọn, dùng để chọn đúng kênh khi chuyển qua lại giữa màn hình thanh toán và màn hình sp
            this.x_id_pos_channel_sale_online = options.x_id_pos_channel_sale_online || 0    // Trường này lưu dữ liệu kênh online khi đồng bộ đơn online
            this.x_check_on_click = options.x_check_on_click || 0                            // Trường này dùng làm cờ dấu cho hành động click select channel để tải lại dữ liệu CTKM, chỉ có ý nghĩa với logic code, không có giá trị về mặt dữ liệu logic
            order.prototype.initialize.apply(this, arguments)
            return this
        },

        init_from_JSON: function (json) {
            this.x_id_pos_channel = json.x_id_pos_channel
            this.x_select_channel_value = json.x_select_channel_value
            this.x_id_pos_channel_sale_online = json.x_id_pos_channel_sale_online
            order.prototype.init_from_JSON.call(this, json)
        },

        export_as_JSON: function () {
            let json = order.prototype.export_as_JSON.apply(this, arguments)
            json.x_id_pos_channel = this.get_x_id_pos_channel()
            json.x_select_channel_value = this.get_x_select_channel_value()
            json.x_id_pos_channel_sale_online = this.get_x_id_pos_channel_sale_online()
            return json
        },

        get_x_id_pos_channel: function () {
            return this.x_id_pos_channel
        },

        get_x_select_channel_value: function () {
            return this.x_select_channel_value
        },

        get_x_id_pos_channel_sale_online: function () {
            return this.x_id_pos_channel_sale_online
        }
    })
})