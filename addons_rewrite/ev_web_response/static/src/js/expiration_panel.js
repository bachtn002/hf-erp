odoo.define("web_enterprise.ExpirationPanel", function (require) {
    "use strict";

    const { Component, hooks } = owl;
    const { useState, useRef } = hooks;
    class ExpirationPanel extends Component {
        constructor() {
            super(...arguments);


        }

        mounted() {

        }
        static computeDiffDays(date) {

        }


        _clearState() {
            for (const key in this.state) {
                delete this.state[key];
            }
        }

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         */
        _onHide() {
            this.trigger("hide-expiration-panel");
        }

        /**
         * @private
         */
        _onClickRegister() {
            this.state.displayRegisterForm = !this.state.displayRegisterForm;
        }

        /**
         * @private
         */
        async _onBuy() {

        }

        /**
         * Save the registration code then triggers a ping to submit it.
         * @private
         */
        async _onCodeSubmit() {

        }

        /**
         * @private
         */
        async _onCheckStatus() {

        }

        /**
         * @private
         */
        async _onSendUnlinkEmail() {

        }

        /**
         * @private
         */
        async _onRenew() {

        }

        /**
         * @private
         */
        async _onUpsell() {

        }
    }

    ExpirationPanel.template = "DatabaseExpirationPanel";

    return ExpirationPanel;
});
