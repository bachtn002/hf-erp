odoo.define('ev_pos_voucher_ui.EditListInputVoucher', function(require) {
    'use strict';

    const EditListInput = require('point_of_sale.EditListInput');
    const Registries = require('point_of_sale.Registries');

    let EditListInputVoucher = EditListInput =>
		class extends EditListInput {
            onKeyup(event) {
                if (event.key === "Enter") {
                    this.trigger('create-new-item');
                }
            }
        }
    Registries.Component.extend(EditListInput, EditListInputVoucher);

    return EditListInput;
});
