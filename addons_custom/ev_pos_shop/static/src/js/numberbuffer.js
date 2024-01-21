odoo.define('ev_pos_shop.PSNumpadInputButton', function (require) {
    "use strict"

    const PSNumpadInputButton = require('point_of_sale.PSNumpadInputButton');
    const Registries = require('point_of_sale.Registries');

    let PSNumpadInputButtonDisable = PSNumpadInputButton =>
        class extends PSNumpadInputButton {
            get hasNumpadMinus() {
                if(this.props.value == '-' && this.env.pos.config.x_enable_lunisolar == false){
                    return false;
                } else {
                    return true;
                }
            }
        }
    Registries.Component.extend(PSNumpadInputButton, PSNumpadInputButtonDisable);

    return PSNumpadInputButton;
});