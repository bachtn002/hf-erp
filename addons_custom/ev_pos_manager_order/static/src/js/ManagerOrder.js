odoo.define('ev_pos_manager_order.OrderlineDetails', function (require) {
    "use strict"


    const OrderlineDetails = require('point_of_sale.OrderlineDetails');
    const Registries = require('point_of_sale.Registries');
    const core = require('web.core');
    const _t = core._t;

    let PosManagerOrder = OrderlineDetails =>
        class extends OrderlineDetails {
            get pricePerUnit() {
                let at = _.str.sprintf(_t("at"))
                return ` ${this.unit} ${at} ${this.env.pos.format_currency_no_symbol(this.unitPrice)} / ${this.unit}`;
            }
        };

    Registries.Component.extend(OrderlineDetails, PosManagerOrder);

    return OrderlineDetails;
});