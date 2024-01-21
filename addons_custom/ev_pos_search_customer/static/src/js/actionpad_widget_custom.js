odoo.define('ev_pos_search_customer.ActionpadWidgetCustom', function (require) {
    "use strict"
    const core = require('web.core');
    // const ProductScreen = require('point_of_sale.ProductScreen');
    const ActionpadWidget = require('point_of_sale.ActionpadWidget');
    const Registries = require('point_of_sale.Registries');

    let ActionpadWidgetCustom = ActionpadWidget =>
        class extends ActionpadWidget {
            constructor() {
                super(...arguments);
                this.handleOnClickSearchCustomer = this.handleOnClickSearchCustomer.bind(this);
            }

            //hàm cập nhật CTKM trên POS gọi callback tới pos_promotion
            handleOnClickSearchCustomer(ev, promotions) {
                console.log('test check onclick')
            }

        };
    Registries.Component.extend(ActionpadWidget, ActionpadWidgetCustom);

    return ActionpadWidget;
});