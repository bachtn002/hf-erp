odoo.define('ev_pos_receipt.Receipt', function (require) {
    "use strict"

    const core = require('web.core');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const PosDB = require('point_of_sale.DB');
    const {debounce} = owl.utils;
    const {useState} = owl.hooks;
    const {useListener} = require('web.custom_hooks');
    const _t = core._t;
    const rpc = require('web.rpc');
    var models = require('point_of_sale.models');
    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_for_printing: function () {
            var result = _super_order.export_for_printing.apply(this, arguments);
            var addressShop_search = this.get_address_shop();
            var nameShop = this.get_name_shop();
            if (this.get_client()) {
                var customer_name = this.get_client().name;
                var customer_phone = this.get_client().phone
            }
            var codeShop = this.get_code_shop();
            var cashier = this.pos.get_cashier();
            var cashier1 = this.pos.employee;
            if (addressShop_search) {
                result.addressShop_search = this.pos.format_currency_no_symbol(addressShop_search);
            }
            if (nameShop) {
                result.name_shop = this.pos.format_currency_no_symbol(nameShop);
            }
            if (codeShop) {
                result.code_shop = this.pos.format_currency_no_symbol(codeShop);
            }
            if (customer_name) {
                result.customer_name = this.pos.format_currency_no_symbol(customer_name)
            }
            if (customer_phone) {
                result.customer_phone = this.pos.format_currency_no_symbol(customer_phone)
            }
            // result.orderlines.forEach((line)=>{
            //     console.log('line', line.getPromotionId())
            //     line.get_product_test()
            // })
            return result;
        },
        get_address_shop: function () {
            return this.pos.config.x_address_shop
        },
        get_name_shop: function () {
            return this.pos.config.x_name_shop
        },
        get_code_shop: function () {
            return this.pos.config.x_code_shop
        },
        initialize_validation_date: function () {
            this.validation_date = new Date();
            this.formatted_validation_date = moment(this.validation_date).format('DD/MM/YYYY HH:mm')
        },
    });
});
