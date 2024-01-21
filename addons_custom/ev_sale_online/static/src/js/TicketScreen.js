odoo.define("ev_sale_online.TicketScreen", function (require) {
    "use strict";

    const core = require('web.core');
    const Registries = require('point_of_sale.Registries');
    const TicketScreen = require('point_of_sale.TicketScreen');
    const { useListener } = require('web.custom_hooks');

    const _t = core._t;
    const rpc = require('web.rpc');

    let TicketScreenSaleOnline = TicketScreen =>
        class extends TicketScreen {
            constructor() {
                super(...arguments);
                this.check_call = false;
            }

            _sync_order_online(){
                var self = this;
                var config_id = self.env.pos.config_id;
                var fields = self.env.pos._get_field_product();
                return new Promise(function (resolve, reject) {
                    self.rpc({
                        model: 'sale.online',
                        method: 'sync_orders_online',
                        args: [config_id, fields],
                    }, {
                        timeout: 10000,
                        shadow: true,
                    })
                    .then(function (orders) {
                        if (self.env.pos.sync_list_order(orders)) {
                            resolve();
                        } else {
                            reject('No online orders!');
                        }
                    }, function (type, err) { reject(); });
                });
            }

            async syncOrderOnline(){
                try {
                    if(this.check_call == true){
                        return;
                    }
                    this.check_call = true;
                    await this._sync_order_online();
                    this.check_call = false;
                    this.render();
                } catch (error) {
                    this.check_call = false;
                    if (error == undefined) {
                        await this.showPopup('OfflineErrorPopup', {
                            title: this.env._t('Offline'),
                            body: this.env._t('Unable to sync Order Online.'),
                        });
                    }
                }
            }
        }
    Registries.Component.extend(TicketScreen, TicketScreenSaleOnline);
    return TicketScreen;
});