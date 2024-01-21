odoo.define('point_of_sale.EditListInputCustom', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class EditListInputCustom extends PosComponent {
        onKeyup(event) {
            if (event.key === "Enter" && event.target.value.trim() !== '') {
                this.trigger('create-new-item');
            }
        }
    }
    EditListInputCustom.template = 'EditListInputCustom';

    Registries.Component.add(EditListInputCustom);

    return EditListInputCustom;
});
