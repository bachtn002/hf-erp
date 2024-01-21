odoo.define('ev_account_sinvoice.models', function (require) {
    'use strict'

    let models = require('point_of_sale.models')

    let order = models.Order
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            this.x_sinvoice_vat = options.x_sinvoice_vat || ''
            this.x_sinvoice_company_name = options.x_sinvoice_company_name || ''
            this.x_sinvoice_address = options.x_sinvoice_address || ''
            this.x_sinvoice_email = options.x_sinvoice_email || ''
            order.prototype.initialize.apply(this, arguments)
            return this
        },

        init_from_JSON: function (json) {
            this.x_sinvoice_vat = json.x_sinvoice_vat
            this.x_sinvoice_company_name = json.x_sinvoice_company_name
            this.x_sinvoice_address = json.x_sinvoice_address
            this.x_sinvoice_email = json.x_sinvoice_email
            order.prototype.init_from_JSON.call(this, json)
        },

        export_as_JSON: function () {
            let json = order.prototype.export_as_JSON.apply(this, arguments)
            json.x_sinvoice_vat = this.get_x_sinvoice_vat()
            json.x_sinvoice_company_name = this.get_x_sinvoice_company_name()
            json.x_sinvoice_address = this.get_x_sinvoice_address()
            json.x_sinvoice_email = this.get_x_sinvoice_email()
            return json
        },
        get_x_sinvoice_vat: function () {
            return this.x_sinvoice_vat
        },
        get_x_sinvoice_company_name: function () {
            return this.x_sinvoice_company_name
        },
        get_x_sinvoice_address: function () {
            return this.x_sinvoice_address
        },
        get_x_sinvoice_email: function () {
            return this.x_sinvoice_email
        }
    })
})