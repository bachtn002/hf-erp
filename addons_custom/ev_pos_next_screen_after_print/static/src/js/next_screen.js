odoo.define('ev_pos_next_screen_after_print.pos_next_screen', function (require) {
    "use strict";

    const models = require('point_of_sale.models');
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');
    let ReceiptScreenCustom = ReceiptScreen =>
        class extends ReceiptScreen {
            async printReceipt() {
                const isPrinted = await this._printReceipt();
                if (isPrinted) {
                    this.currentOrder._printed = true;
                    this.orderDone();
                }
            }
        };
    Registries.Component.extend(ReceiptScreen, ReceiptScreenCustom);

    return ReceiptScreen;
});