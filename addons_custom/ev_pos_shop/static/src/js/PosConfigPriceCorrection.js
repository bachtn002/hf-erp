odoo.define('ev_pos_shop.NumpadWidget', function (require) {
    "use strict"


    const NumpadWidget = require('point_of_sale.NumpadWidget');
    const Registries = require('point_of_sale.Registries');

    let PriceCorrection = NumpadWidget =>
        class extends NumpadWidget {
            get hasPriceControlRights() {
                return this.env.pos.config.x_price_correction;
            }

            get hasNumpadMinus() {
                return this.env.pos.config.x_enable_lunisolar;
            }

        };

    Registries.Component.extend(NumpadWidget, PriceCorrection);

    return PriceCorrection;
});