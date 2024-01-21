odoo.define('ev_sale_online_miniapp.models', function (require) {
    'use strict'

    const models = require("point_of_sale.models")

    let order = models.Order
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            this.is_created_by_api = options.is_created_by_api || null
            this.loyalty_point_redeem = options.loyalty_point_redeem || null
            this.payment_info_sale_online = options.payment_info_sale_online || null
            this.x_buyer_not_get_invoice = options.x_buyer_not_get_invoice || ''
            this.order_line_info = options.order_line_info || null
            this.discount_on_bill = options.discount_on_bill || null
            this.discount_on_product = options.discount_on_product || null
            this.is_applied_promotion = options.is_applied_promotion || false
            this.check_is_not_allow_editing = options.check_is_not_allow_editing || false
            this.write_date = options.write_date || null
            this.id_sale_online = options.id_sale_online || null
            this.state_sale_online = options.state_sale_online || null
            this.total_discount_on_bill = options.total_discount_on_bill || null
            this.product_km_id = options.product_km_id || null
            order.prototype.initialize.apply(this, arguments)
            return this
        },
        init_from_JSON: function (json) {
            this.is_created_by_api = json.is_created_by_api
            this.loyalty_point_redeem = json.loyalty_point_redeem
            this.payment_info_sale_online = json.payment_info_sale_online
            this.x_buyer_not_get_invoice = json.x_buyer_not_get_invoice
            this.order_line_info = json.order_line_info
            this.discount_on_bill = json.discount_on_bill
            this.discount_on_product = json.discount_on_product
            this.is_applied_promotion = json.is_applied_promotion
            this.check_is_not_allow_editing = json.check_is_not_allow_editing
            this.write_date = json.write_date
            this.id_sale_online = json.id_sale_online
            this.state_sale_online = json.state_sale_online
            this.total_discount_on_bill = json.total_discount_on_bill
            this.product_km_id = json.product_km_id
            order.prototype.init_from_JSON.call(this, json)
        },
        export_as_JSON: function () {
            let json = order.prototype.export_as_JSON.apply(this, arguments)
            json.is_created_by_api = this.get_is_created_by_api()
            json.loyalty_point_redeem = this.get_loyalty_point_redeem()
            json.payment_info_sale_online = this.get_payment_info_sale_online()
            json.x_buyer_not_get_invoice = this.get_x_buyer_not_get_invoice()
            json.order_line_info = this.get_order_line_info()
            json.discount_on_bill = this.get_discount_on_bill()
            json.discount_on_product = this.get_discount_on_product()
            json.is_applied_promotion = this.get_is_applied_promotion()
            return json
        },
        get_is_created_by_api: function () {
            return this.is_created_by_api
        },
        get_loyalty_point_redeem: function () {
            return this.loyalty_point_redeem
        },
        get_payment_info_sale_online: function () {
            return this.payment_info_sale_online
        },
        get_x_buyer_not_get_invoice: function () {
            return this.x_buyer_not_get_invoice
        },
        get_order_line_info: function () {
            return this.order_line_info
        },
        get_discount_on_bill: function () {
            return this.discount_on_bill
        },
        get_discount_on_product: function () {
            return this.discount_on_product
        },
        get_is_applied_promotion: function () {
            return this.is_applied_promotion
        },
        add_paymentline: function (payment_method) {
            this.assert_editable()
            var newPaymentline = new models.Paymentline({}, {
                order: this,
                payment_method: payment_method,
                pos: this.pos
            })
            if (payment_method.is_cash_count_zero) {
                newPaymentline.set_amount(0)
            }
            if (!payment_method.is_cash_count_zero) {
                newPaymentline.set_amount(this.get_due())
            }
            if (this.is_created_by_api || !this.is_created_by_api) {
                if (this.payment_info_sale_online) {
                    this.payment_info_sale_online.forEach((item) => {
                        if (item[0] === payment_method['id']) {
                            newPaymentline.set_amount(item[1])
                            return
                        }
                    })
                }
            }

            this.paymentlines.add(newPaymentline)
            this.select_paymentline(newPaymentline)
            return newPaymentline
        },
        scan_product: function (parsed_code) {
            var selectedOrder = this.get_order();
            // chặn quét barcode trên kênh online không cho phép sửa
            if (selectedOrder.sale_online) {
                var channel_current = this.list_pos_channel_online.filter((i) => {
                    return (i.id === selectedOrder.x_id_pos_channel_sale_online)
                })
                if (selectedOrder.is_created_by_api) {
                    return true
                } else if (channel_current[0]['is_not_allow_editing']) {
                    return true
                } else {
                }
            }

            var product = this.db.get_product_by_barcode(parsed_code.base_code);

            if (!product) {
                return false;
            }

            if (parsed_code.type === 'price') {
                selectedOrder.add_product(product, {price: parsed_code.value});
            } else if (parsed_code.type === 'weight') {
                selectedOrder.add_product(product, {quantity: parsed_code.value, merge: false});
            } else if (parsed_code.type === 'discount') {
                selectedOrder.add_product(product, {discount: parsed_code.value, merge: false});
            } else {
                selectedOrder.add_product(product);
            }
            return true;
        },
    })

    return models
})