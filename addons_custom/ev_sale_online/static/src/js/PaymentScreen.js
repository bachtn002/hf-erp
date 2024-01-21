odoo.define("ev_sale_online.PaymentScreen", function (require) {
    "use strict";

    const core = require('web.core');
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const { useListener } = require('web.custom_hooks');

    const _t = core._t;
    const rpc = require('web.rpc');

    let PaymentScreenNote = PaymentScreen =>
        class extends PaymentScreen {
            async _finalizeValidation() {
                try {
                    //await this._check_online();
                    var self = this;
                    var order = this.currentOrder;
                    var orderlines = order.get_orderlines();
                    for(var i = 0; i < orderlines.length; i++){
                        var line = orderlines[i];
                        if(line.quantity == 0){
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Thông báo'),
                                body: this.env._t('Trong đơn hàng có sản phẩm số lượng bằng 0. Hãy quay lại và xóa khỏi đơn hàng.'),
                            });
                            return false;
                        }
                    }
                    var note = $('#note').val();
                    order.set_note(note);
                    super._finalizeValidation();
                } catch (error) {
                    if (error == undefined) {
                        await this.showPopup('OfflineErrorPopup', {
                            title: this.env._t('Offline'),
                            body: this.env._t('Losing the connection.'),
                        });
                    } else {
                        await this.showPopup('OfflineErrorPopup', {
                            title: this.env._t('Error'),
                            body: error,
                        });
                    }
                }
            }

            _check_online() {
                var self = this;
                return new Promise(function (resolve, reject) {
                    self.rpc({
                        model: 'pos.config',
                        method: 'check_online',
                        args: [],
                    }, {
                        timeout: 3000,
                        shadow: true,
                    })
                    .then(function (online) {
                        if (online) {
                            resolve();
                        } else {
                            reject('No internet!');
                        }
                    }, function (type, err) { reject(); });
                });
            }
        }

    Registries.Component.extend(PaymentScreen, PaymentScreenNote);
    return PaymentScreen;
});