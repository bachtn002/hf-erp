odoo.define('ev_pos_voucher_ui.VoucherPopup', function (require) {
    'use strict';

    const {useState} = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const {useAutoFocusToLast} = require('point_of_sale.custom_hooks');

    class VoucherPopup extends AbstractAwaitablePopup {
        /**
         * @param {String} title required title of popup
         * @param {Array} [props.array=[]] the array of { id, text } to be edited or an array of strings
         * @param {Boolean} [props.isSingleItem=false] true if only allowed to edit single item (the first item)
         */
        constructor() {
            super(...arguments);
            this._id = 0;
            this.state = useState({array: this._initialize(this.props.array)});
            useAutoFocusToLast();
        }

        async confirm() {
            this.props.resolve({
                confirmed: true,
                payload: await this.getPayload(),
                check_product: await this.check_product()
            });
            this.trigger('close-popup');
        }

        _nextId() {
            return this._id++;
        }

        _emptyItem() {
            return {
                text: '',
                _id: this._nextId(),
            };
        }

        _initialize(array) {
            // If no array is provided, we initialize with one empty item.
            if (array.length === 0) return [this._emptyItem()];
            // Put _id for each item. It will serve as unique identifier of each item.
            return array.map((item) => Object.assign({}, {_id: this._nextId()}, typeof item === 'object' ? item : {'text': item}));
        }

        removeItem(event) {
            const itemToRemove = event.detail;
            this.state.array.splice(
                this.state.array.findIndex(item => item._id == itemToRemove._id),
                1
            );
            // We keep a minimum of one empty item in the popup.
            if (this.state.array.length === 0) {
                this.state.array.push(this._emptyItem());
            }
        }

        createNewItem() {
            if (this.props.isSingleItem) return;
            this.state.array.push(this._emptyItem());
        }

        /**
         * @override
         */
        getPayload() {
            return {
                newArray: this.state.array
                    .filter((item) => item.text.trim() !== '')
                    .map((item) => Object.assign({}, item)),
            };
        }

        async check_product() {
            let payload = this.getPayload()
            var customerID = false;
            const order = this.props.order;
            if (order.get_client()) {
                customerID = order.get_client().id;
            }
            this.state.product_id = false
            if (payload['newArray'].length > 0) {
                let id = payload['newArray'][0]['_id']
                let name = payload['newArray'][0]['text']
                let args = [id, name, customerID];
                var ifConnected = window.navigator.onLine;
                if (!ifConnected) {
                    this.state.message = '* Đường truyền mạng có vấn đề. Vui lòng kiểm tra lại!';
                    this.playSound('error');
                }
                const result = await this.rpc({
                    model: 'stock.production.lot',
                    method: 'check_code_from_ui',
                    args: args,
                }).then((response) => {
                    if ('product_id' in response) {
                        this.state.product_id = response['product_id']
                    }
                });
            }
            return this.state.product_id
        }

        async onClickButtonVoucher(ev) {
            let payload = this.getPayload()
            var customerID = false;
            const order = this.props.order;
            if (order.get_client()) {
                customerID = order.get_client().id;
            }
            this.state.message = undefined;
            let product_id = false
            if (payload['newArray'].length > 0) {
                let id = payload['newArray'][0]['_id']
                let name = payload['newArray'][0]['text']
                let args = [id, name, customerID];
                var ifConnected = window.navigator.onLine;
                if (!ifConnected) {
                    this.state.message = '* Đường truyền mạng có vấn đề. Vui lòng kiểm tra lại!';
                    this.playSound('error');
                }
                const result = await this.rpc({
                    model: 'stock.production.lot',
                    method: 'check_code_from_ui',
                    args: args,
                }).then((response) => {
                    if ('message' in response) {
                        this.state.message = '* ' + response['message'];
                        this.playSound('error');
                    } else {
                        var product = this.env.pos.db.get_product_by_id(response['product_id'])
                        if (product == undefined) {
                            this.state.message = '* Voucher/coupon chưa được cấu hình bán trên POS. Vui lòng kiểm tra lại!'
                            this.playSound('error');
                        }
                    }
                });
            } else {
                this.state.message = '* Xin vui lòng nhập mã voucher!'
                this.playSound('error');
            }
            ;
            if (this.state.message == undefined) {
                await this.confirm()
            }
            ;

        }
    }

    VoucherPopup.template = 'VoucherPopup';
    VoucherPopup.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        array: [],
        isSingleItem: false,
    };

    Registries.Component.add(VoucherPopup);

    return VoucherPopup;
});