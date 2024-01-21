odoo.define('ev_pos_next_screen_after_print.ClientLineCustom', function (require) {
    'use strict';

    const Registries = require('point_of_sale.Registries');
    const ClientLine = require('point_of_sale.ClientLine');

    let ClientLineCustom = ClientLine =>
        class extends ClientLine {
            get hide_edit_button() {
                return this.env.pos.config.x_apply_fix_customer
            }
        };

    Registries.Component.extend(ClientLine, ClientLineCustom);

    return ClientLine;
});
