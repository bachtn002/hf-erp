odoo.define('ev_pos_search_customer.ActionpadWidget', function (require) {
    "use strict"

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const ActionpadWidget = require('point_of_sale.ActionpadWidget');

    let ActionpadWidgetSearchCustomer = ActionpadWidget =>
        class extends ActionpadWidget {
            constructor() {
                super(...arguments);
                this.upDatePromotion = this.upDatePromotion.bind(this);
            }

            upDatePromotion(ev, promotions){
                this.props.upDatePromotion(ev, promotions);
            }

        }

    Registries.Component.extend(ActionpadWidget, ActionpadWidgetSearchCustomer);
    return ActionpadWidget;
});