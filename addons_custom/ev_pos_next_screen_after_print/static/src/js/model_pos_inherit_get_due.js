odoo.define('ev_pos_next_screen_after_print.Order', function (require) {
    "use strict"

    const models = require('point_of_sale.models');
    var utils = require('web.utils');
    var round_pr = utils.round_precision;
    var _superOrder = models.Order;
    var exports = {};
    models.Order = models.Order.extend({
        //hiển thị số tiền là 0 với phương thức thanh toán là tiền mặt
        add_paymentline: function (payment_method) {
            this.assert_editable();
            var newPaymentline = new models.Paymentline({}, {
                order: this,
                payment_method: payment_method,
                pos: this.pos
            });
            if (payment_method.is_cash_count_zero) {
                newPaymentline.set_amount(0);
            }
            if (!payment_method.is_cash_count_zero) {
                newPaymentline.set_amount(this.get_due());
            }
            this.paymentlines.add(newPaymentline);
            this.select_paymentline(newPaymentline);
            return newPaymentline;
        },
    })
    return models;
})