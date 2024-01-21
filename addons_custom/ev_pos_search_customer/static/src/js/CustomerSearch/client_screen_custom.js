odoo.define('ev_pos_search_customer.ClientScreenCustom', function (require) {
    "use strict"
    const core = require('web.core');
    const ClientListScreen = require('point_of_sale.ClientListScreen');
    const Registries = require('point_of_sale.Registries');
    const _t = core._t;

    let ClientScreenCustom = ClientListScreen =>
        class extends ClientListScreen {
            constructor() {
                super(...arguments);
            }

            get nextButton() {
                if (!this.props.client) {
                    return {command: 'set', text: _t('Set Customer')};

                } else if (this.props.client && this.props.client === this.state.selectedClient) {
                    return {command: 'deselect', text: _t('Deselect Customer')};
                } else {
                    return {command: 'set', text: _t('Change Customer')};
                }
            }

            back() {
                this.props.resolve({confirmed: false, payload: false});
                this.trigger('close-temp-screen');
            }


        };
    Registries.Component.extend(ClientListScreen, ClientScreenCustom);

    return ClientListScreen;
});