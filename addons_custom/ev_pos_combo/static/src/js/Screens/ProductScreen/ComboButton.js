odoo.define('ev_pos_combo.ComboButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');


    class ComboButton extends PosComponent {

        get isCombo() {
            return this.props.line.get_product().x_is_combo &&
                this.props.line.get_product().x_product_combo_ids.length > 0 &&
                this.env.pos.config.x_enable_combo
        }

        _onClickComboButton() {
            this.showPopup('PopupCombo', {line: this.props.line});
        }
    }

    ComboButton.template = 'ComboButton';

    Registries.Component.add(ComboButton);

    return ComboButton;
});
