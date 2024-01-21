odoo.define('ev_pos_toggle_numpad.ToggleControllButton', function (require) {
    "use strict";

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const {useState} = owl.hooks;


    class ToggleControllButton extends PosComponent {

        constructor() {
            super(...arguments);
            this.state = useState({isShow: true});
        }

        onClick = (ev) => {
            ev.preventDefault();
            let buttonEl = $('.control-button');
            buttonEl.toggleClass('hide-text');
            if (buttonEl.hasClass('hide-text')) {
                buttonEl.find('span').css({'display': 'none'});
            } else {
                setTimeout(function () {
                    buttonEl.find('span').css({'display': 'inline-block', 'font-weight': 'bold'});
                }, 300);
            }
            this.state.isShow = !this.state.isShow;
        }
    };

    ToggleControllButton.template = 'ToggleControllButton';

    Registries.Component.add(ToggleControllButton);

    return ToggleControllButton;

});
