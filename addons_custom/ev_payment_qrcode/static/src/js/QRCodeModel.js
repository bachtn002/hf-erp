odoo.define('ev_payment_qrcode.QRCodeModel', function (require) {
    'use strict'

    const models = require('point_of_sale.models')
    models.load_fields('pos.payment.method', ['is_qrcode_payment'])
    models.load_models([{
        model: 'pos.shop',
        label: 'pos.shop',
        field: ['merchant_id'],
        domain: function (self) {
            return self.pos_session.id
                ? [['id', '=', self.pos_session.x_pos_shop_id[0]]]
                : [['id', 'in', []]];
        },
        loaded: (self, res) => {
            self.merchant_id = res[0].merchant_id
            self.current_interval = []       // Field reset interval expired_time_qrcode
            self.data_for_mbpay_paygate_detail = []
            self.pg_order_reference = ''
        }
    }])
    var order_model_super = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function(attr, options) {
            order_model_super.initialize.call(this,attr,options);
            this.check_create_qrcode_first_time = this.check_create_qrcode_first_time || false
            this.is_calling_qrcode_payment = this.is_calling_qrcode_payment || false
        },
    })
})