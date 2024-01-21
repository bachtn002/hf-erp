odoo.define('ev_pos_voucher_ui.EditListPopup', function (require) {
    'use strict';

    const EditListPopup = require('point_of_sale.EditListPopup');
    const Registries = require('point_of_sale.Registries');

    let EditListPopupVoucher = EditListPopup =>
        class extends EditListPopup {

            async check() {
                let payload = await this.getPayload();
                this.state.message = undefined;
                let product_id = 0;
                var customerID = false;
                const order = this.props.order;
                if (order.get_client() != undefined) {
                    customerID = order.get_client().id;
                }
                if (payload['newArray'].length > 0) {
                    let id = payload['newArray'][0]['_id'];
                    let name = payload['newArray'][0]['text'];
                    let args = [id, name, customerID];
                    var ifConnected = window.navigator.onLine;
                    if (!ifConnected) {
                        this.state.message = '* Đường truyền mạng có vấn đề. Vui lòng kiểm tra lại!';
                        this.playSound('error');
                    }
                    await this.rpc({
                        model: 'stock.production.lot',
                        method: 'check_code_from_ui',
                        args: args,
                    }).then((response) => {
                        if ('message' in response) {
                            this.state.message = '* ' + response['message']
                            this.playSound('error');
                        } else {
                            product_id = response['product_id']
                        }
                    });
                } else {
                    this.state.message = '* Xin vui lòng nhập mã voucher!';
                    this.playSound('error');
                }
                ;
                if (this.props.product.id != product_id) {
                    this.state.message = '* Bạn đã nhập sai mã voucher. Vui lòng nhập lại!';
                    this.playSound('error');
                }
                if (this.state.message == undefined) {
                    await this.confirm()
                }
                ;
            }
        }
    Registries.Component.extend(EditListPopup, EditListPopupVoucher);

    return EditListPopup;
});
