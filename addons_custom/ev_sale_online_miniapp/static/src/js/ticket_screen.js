odoo.define('ev_sale_online_miniapp.TicketScreen', function (require) {
    'use strict'
    const core = require('web.core')
    const Registries = require('point_of_sale.Registries')
    const TicketScreen = require('point_of_sale.TicketScreen')
    const {useListener} = require('web.custom_hooks')
    const _t = core._t
    const rpc = require('web.rpc')

    let TicketScreenMiniApp = TicketScreen => class extends TicketScreen {
        constructor() {
            super(...arguments)
        }

        selectOrder(order) {
            super.selectOrder(order)
            order.sale_online ? (() => {
                if (order.is_applied_promotion) return
                order.is_applied_promotion = true
                let listPromotions = this.getValidPromotions(order, order.x_id_pos_channel_sale_online)
                order.discount_on_product ? (() => {
                    order.discount_on_product.forEach((item) => {
                        let product = self.posmodel.db.get_product_by_id(item['product_id'])
                        let options = {
                            price: item['discount'] * -1,
                            quantity: 1,
                            merge: false,
                            extras: {
                                promotion_id: parseInt(item['promotion_id']),
                                promotion_code: item['promotion_code'],
                                x_product_promotion: item['x_product_promotion'],
                            }
                        }
                        // Tìm vị trí của sp tương ứng được áp dụng KM
                        var index = order.orderlines.length
                        for (var i = 0; i < order.orderlines.length; i++) {
                            if (order.orderlines.models[i].product.default_code === item.product_code) {
                                index = i + 1;
                                break
                            }
                        }
                        order.add_product(product, options)

                        // Chuyển sp KM vừa thêm lên vị trí index
                        if (index !== order.orderlines.length - 1) {
                            let lastLine = order.orderlines.models.pop();
                            order.orderlines.models.splice(index, 0, lastLine);
                        }
                    })
                })() : null

                order.discount_on_bill ? (() => {
                    order.discount_on_bill.forEach((item) => {
                        let product = self.posmodel.db.get_product_by_id(item['product_id'])
                        let options = {
                            price: item['discount'] * -1,
                            quantity: 1,
                            merge: false,
                            extras: {
                                promotion_id: parseInt(item['promotion_id']),
                                promotion_code: item['promotion_code'],
                                x_product_promotion: item['x_product_promotion'],
                            }
                        }
                        order.add_product(product, options)
                    })
                })() : null


                order.order_line_info && !order.is_created_by_api ? (() => {
                    order.order_line_info.forEach((item) => {
                        parseInt(item[3]) > 0 ? (() => {
                            let product = self.posmodel.db.get_product_by_id(item[1])
                            let options = {
                                price: item[3] * -1,
                                quantity: 1,
                                merge: false,
                                extras: {
                                    promotion_code: item[2],
                                }
                            }
                            // Tìm vị trí của sp tương ứng được áp dụng KM
                            var index = order.orderlines.length
                            for (var i = 0; i < order.orderlines.length; i++) {
                                if (order.orderlines.models[i].product.id === item[0]) {
                                    index = i + 1;
                                    break
                                }
                            }
                            order.add_product(product, options)

                            // Chuyển sp KM vừa thêm lên vị trí index
                            if (index !== order.orderlines.length - 1) {
                                let lastLine = order.orderlines.models.pop();
                                order.orderlines.models.splice(index, 0, lastLine);
                            }
                        })() : null
                    })
                })() : null

                parseInt(order.total_discount_on_bill) && !order.is_created_by_api > 0 ? (() => {
                    let product = self.posmodel.db.get_product_by_id(order.product_km_id)
                    let options = {
                        price: parseInt(order.total_discount_on_bill) * -1,
                        quantity: 1,
                        merge: false,
                    }
                    order.add_product(product, options)
                })() : null

                listPromotions.forEach((p) => {
                    p.applyPromotionToOrder(order)
                })

                // Ghi thông tin hoá đơn điên tử lên bill
                order.x_buyer_not_get_invoice == 11 ? order.set_is_get_invoice(true) : null
                let client = this.env.pos.get_client()
                if (client){
                    let name = client.name
                    if (!name.includes(client.phone))
                        client.name = name + ' - ' + client.phone
                }

            })() : null
            order.sale_online && order.loyalty_point_redeem > 0 ? (() => {
                let check_tl = true
                order.orderlines.models.forEach((i) => {
                    i.product.default_code === 'TL' ? (check_tl = false, null) : null
                })
                return check_tl ? (() => {
                    // if (order.loyalty_point_redeem > order.get_new_total_points() && order.get_new_total_points() !== 0) {
                    //     this.showPopup('ErrorPopup', {
                    //         title: this.env._t('Lỗi'),
                    //         body: this.env._t('Vui lòng nhập điểm nhỏ hơn điểm tích lũy'),
                    //     })
                    //     return
                    // }
                    let rule_program = order.get_amount_rule_custom()
                    let x_discount_amount = rule_program.x_discount_amount
                    let x_point_cost = rule_program.x_point_cost
                    let price_discount = order.loyalty_point_redeem * x_discount_amount / x_point_cost
                    this.env.pos.get_order().apply_reward_custom(price_discount)
                })() : null
            })() : null
        }

        getValidPromotions(order, select_channel_value) {
            order = order || this.get_order()
            order.orderlines.length < 1 ? [] : null
            let promotions = self.posmodel.getPromotions()
            promotions = self.posmodel.getPromotions().filter((item) => {
                return item.pos_channel_ids.includes(parseInt(select_channel_value)) && (item['type'] === 'game_total_amount' || item['type'] === 'gift_code_total_amount' || item['type'] === 'gift_code_product_qty' || item['type'] === 'loyalty_point')
            })
            return promotions.filter((item) => {
                return item.isValidOrder(order, false)
            })
        }


    }
    Registries.Component.extend(TicketScreen, TicketScreenMiniApp)
    return TicketScreen
})