odoo.define('ev_pos_loyalty_custom.ButtonLoyaltyCustom', function (require) {
    "use strict"

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    var models = require('point_of_sale.models');
    var _super = models.Order;
    let PosModel = models.PosModel;
    models.PosModel = PosModel.extend({
        initialize: function (session, attributes) {
            var self = this;
            PosModel.prototype.initialize.call(this, session, attributes);
        },

        search_loyalty_partner: function (partner_id) {
            var self = this;
            let args = [partner_id, partner_id]
            return this.rpc({
                model: 'res.partner',
                method: 'search_loyalty_points',
                args: args,
            }, {
                timeout: 3000,
                shadow: true,
            })
        },


    });
    models.Order = models.Order.extend({
        get_spent_points: function () {
            if (!this.pos.loyalty || !this.get_client()) {
                return 0;
            } else {
                var points = 0;
                var rule_program = this.pos.loyalty
                var x_discount_amount = rule_program.x_discount_amount;
                for (var line of this.get_orderlines()) {
                    var reward = line.reward_custom_id;
                    let price_loyalty = line.price;

                    if (reward === 'reward') {
                        let point = price_loyalty / x_discount_amount * (-1);
                        points += point;
                    }
                }
                return points;
            }
        },
    })
    let Orderline = models.Orderline;
    var _super_orderline = models.Orderline;
    models.Orderline = models.Orderline.extend({
        init_from_JSON: function (json) {
            Orderline.prototype.init_from_JSON.apply(this, arguments);
            this.reward_custom_id = json.reward_custom_id;
        },
        export_as_JSON: function () {
            let res = Orderline.prototype.export_as_JSON.apply(this, arguments);
            res.reward_custom_id = this.reward_custom_id;
            return res;
        },
    });

    class ButtonLoyaltyCustom extends PosComponent {
        constructor() {
            super(...arguments);
        }

        get currentOrder() {
            return this.env.pos.get_order();
        }

        async onClickButtonLoyaltyCustom(event) {
            const order = this.currentOrder;
            let check_click;
            order.orderlines.forEach((line) => {
                if (line.reward_custom_id === 'reward') {
                    check_click = true;
                }
            });

            const {confirmed, payload} = await this.showPopup("LoyaltyCustomPopup", {
                title: this.env._t('Vui lòng nhập điểm!'),
                order: order
            });
            if (confirmed) {
                const isNumeric = (num) => (typeof (num) === 'number' || typeof (num) === "string" && num.trim() !== '') && !isNaN(num);
                let client = this.env.pos.get('client') || this.env.pos.get_client();
                if (client === null) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Lỗi'),
                        body: this.env._t('Chưa chọn khách hàng'),
                    });
                    return
                }
                let partner_not_applys = this.env.pos.loyalty.res_partner_id_not_apply
                let partner_group_not_applys = this.env.pos.loyalty.res_partner_id_not_apply_group
                let partner_id = this.env.pos.get_order().get_client().id
                let partner_groups = this.env.pos.get_order().get_client().partner_groups[0]
                // check khách hàng không áp dụng
                if (_.indexOf(partner_not_applys, partner_id) != -1) {
                    return
                }
                // check nhóm khách hàng không áp dụng
                if (_.indexOf(partner_group_not_applys, partner_groups) != -1) {
                    return
                }
                // check là sàn thương mại điện tử
                if (this.env.pos.get_order().get_client().x_ecommerce) {
                    return
                }
                let total_user = this.env.pos.get_order().get_client().loyalty_points;
                var self = this;
                let id = this.env.pos.get_order().get_client().id
                let args = [id, id];
                try {
                    this.env.pos.search_loyalty_partner(id);
                    this.rpc({
                        model: 'res.partner',
                        method: 'search_loyalty_points',
                        args: args,
                    }, {
                        timeout: 3000,
                        shadow: true,
                    })
                        .then(function (loyalty_points) {
                            var client = self.env.pos.get_order().get_client();
                            if (client.loyalty_points !== loyalty_points) {
                                this.showPopup('ErrorPopup', {
                                    title: this.env._t('Lỗi'),
                                    body: this.env._t('Điểm tích lũy của khách hàng không đồng bộ với trên server'),
                                });
                                return
                            }
                        });
                } catch (error) {
                    await this.showPopup('OfflineErrorPopup', {
                        title: this.env._t('Offline'),
                        body: this.env._t('Điểm tích lũy của khách hàng không đồng bộ với trên serverr.'),
                    });
                    return
                }
                if (!client) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Lỗi'),
                        body: this.env._t('Chưa chọn khách hàng'),
                    });
                    return
                }
                if (check_click === true) {
                    let order = this.env.pos.get_order();
                    order.orderlines.forEach((line) => {
                        if (line.reward_custom_id === 'reward') {
                            order.remove_orderline(line);
                        }
                    });
                }
                if (total_user === 0) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Lỗi'),
                        body: this.env._t('Khách hàng chưa có điểm tích lũy'),
                    });
                    return
                }
                var point_input = parseInt(payload['newArray'][0]['text'])
                // let test = Number.isInteger(point_input)
                var char = payload['newArray'][0]['text']
                let isnum = /^\d+$/.test(char);

                if (total_user < point_input) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Lỗi'),
                        body: this.env._t('Vui lòng nhập điểm nhỏ hơn điểm tích lũy'),
                    });
                    return
                }
                if (point_input < 0) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Lỗi'),
                        body: this.env._t('Vui lòng nhập điểm lớn hơn 0'),
                    });
                    return
                }
                if (isNaN(point_input) || !isnum) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Lỗi'),
                        body: this.env._t('Giá trị nhập không hợp lệ'),
                    });
                    return
                }

                // let client = this.env.pos.get('client') || this.env.pos.get_client();
                let order = this.env.pos.get_order();
                var rule_program = order.get_amount_rule_custom()
                var x_discount_amount = rule_program.x_discount_amount
                var x_point_cost = rule_program.x_point_cost
                if (x_discount_amount && x_point_cost) {
                    var point_input = parseInt(payload['newArray'][0]['text'])
                    if (point_input > order.get_new_total_points()) {
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Lỗi'),
                            body: this.env._t('Vui lòng nhập điểm nhỏ hơn điểm tích lũy'),
                        });
                        return
                    }
                    // Tiền được giảm khi áp dụng điểm
                    var amount_reduced = point_input / order.pos.loyalty.x_point_cost * order.pos.loyalty.x_discount_amount
                    // Giá trị đơn hàng
                    var order_value = 0
                    for (var line of order.get_orderlines()){
                        order_value += line.get_price_with_tax();
                    }
                    if (amount_reduced > order_value) {
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Lỗi'),
                            body: this.env._t('Vui lòng không nhập điểm lớn hơn giá trị đơn hàng!'),
                        });
                        return
                    }
                    var price_discount = point_input * x_discount_amount / x_point_cost;
                    // await this.env.pos.search_product_to_server(rule_program.product_id[0]);
                    this.currentOrder.apply_reward_custom(price_discount)
                }
            }
        }
    }

    ButtonLoyaltyCustom.template = 'ButtonLoyaltyCustom';
    Registries.Component.add(ButtonLoyaltyCustom);

    return ButtonLoyaltyCustom

});

