odoo.define('ev_account_sinvoice.Orderline', function (require) {
    "use strict"

    const models = require('point_of_sale.models');

    let Orderline = models.Orderline
    models.Orderline = Orderline.extend({

        initialize: function (attributes, options) {
            this.sinvoice_tax_amount = options.sinvoice_tax_amount || 0
            Orderline.prototype.initialize.apply(this, arguments)
            return this
        },

        init_from_JSON: function (json) {
            Orderline.prototype.init_from_JSON.apply(this, arguments);
            this.sinvoice_tax_amount = json.sinvoice_tax_amount
        },
        export_as_JSON: function () {
            let res = Orderline.prototype.export_as_JSON.apply(this, arguments);
            res.sinvoice_tax_amount = this.get_sinvoice_tax_amount()
            return res
        },
        get_sinvoice_tax_amount: function () {
            return this.sinvoice_tax_amount
        },
        set_sinvoice_tax_amount: function (tax_amount) {
            this.sinvoice_tax_amount = tax_amount
        },
    })
    return models
})