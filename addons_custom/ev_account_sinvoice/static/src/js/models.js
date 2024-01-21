odoo.define('ev_account_sinvoice.ResCompany', function (require) {
    'use strict'

    const models = require('point_of_sale.models');

    models.load_fields('res.company', ['sinvoice_search_url']);

    var order_model_super = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function(attr, options) {
            order_model_super.initialize.call(this,attr,options);
            this.is_get_invoice = this.is_get_invoice || false;
        },

        export_for_printing: function () {
            var receipt = order_model_super.export_for_printing.bind(this)();

            receipt = _.extend(receipt, {
                'company': _.extend(receipt.company, {
                    'sinvoice_search_url': this.pos.company.sinvoice_search_url
                })
            });
            receipt.is_get_invoice = this.get_is_get_invoice();
            return receipt;
        },

        set_is_get_invoice: function(is_get_invoice){
            this.is_get_invoice = is_get_invoice;
        },

        get_is_get_invoice: function(){
            return this.is_get_invoice;
        },
    })

});