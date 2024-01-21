odoo.define('ev_pos_voucher_ui.VoucherPromotionPopup', function (require) {
    'use strict';

    const {useState} = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const {useAutoFocusToLast} = require('point_of_sale.custom_hooks');

    class VoucherPromotionPopup extends AbstractAwaitablePopup {
        /**
         * @param {String} title required title of popup
         * @param {Array} [props.array=[]] the array of { id, text } to be edited or an array of strings
         * @param {Boolean} [props.isSingleItem=false] true if only allowed to edit single item (the first item)
         */
        constructor() {
            super(...arguments);
            this._id = 0;
            // this.state = useState({array: this._initialize(this.props.array)});
            useAutoFocusToLast();
            let promotions_all = this.env.pos.getValidPromotions(null, true);
            let promotions = [];
                promotions_all.forEach((pro) => {
                    if (pro.check_promotion) {
                        promotions.push(pro)
                    }
                })
            this.state = useState({
                promotions: promotions,
                array: this._initialize(this.props.array)
            });
        }

        //Caonv
        async onClickApplyPromotionCode(ev) {


            let payload = this.getPayload()
            var customerID = false;
            const order = this.props.order;
            if (order.get_client()) {
                customerID = order.get_client().id;
            }
            this.state.message = undefined;
            if (payload['newArray'].length > 0) {
                let id = payload['newArray'][0]['_id']
                let name = payload['newArray'][0]['text']
                let args = [id, name, customerID];
                var message = false;
                var ifConnected = window.navigator.onLine;
                if (!ifConnected) {
                    this.state.message = '* Đường truyền mạng có vấn đề. Vui lòng kiểm tra lại!';
                    this.playSound('error');
                }
                // const result = await this.rpc({
                //     model: 'promotion.voucher.line',
                //     method: 'check_promotion',
                //     args: args,
                // }).then((response) => {
                //     if ('message' in response) {
                //         // message = response['message'];
                //         this.state.message = '* ' + response['message'];
                //         this.playSound('error');
                //     }
                // });
                let args_code = [order.name, order.name, name];
                const result = await this.rpc({
                    model: 'promotion.voucher.count',
                    method: 'check_promotion_code',
                    args: args_code,
                }).then((response) => {
                    if ('message' in response) {
                        // message = response['message'];
                        this.state.message = '* ' + response['message'];
                        this.playSound('error');
                    }
                });

            } else {
                this.state.message = '* Xin vui lòng nhập mã khuyến mại!'
                this.playSound('error');
            }
            // Sau khi check các trường hợp không hợp lệ thực hiện tiếp
            if (this.state.message == undefined) {
                await this.confirm()
            }

            ev.preventDefault();
            this.props.onClickApplyPromotionCodeCha(ev, 'ABC');
            // this.cancel();
        }

        //End CaoNV

        async confirm() {
            this.props.resolve({
                confirmed: true,
                payload: await this.getPayload(),
                check_promotion: await this.check_promotion(),
                get_promotion_id: await this.get_promotion_id(),
                code_promotion: await this.get_promotion_code(),
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

        async check_promotion() {
            let payload = this.getPayload()
            var customerID = false;
            const order = this.props.order;
            if (order.get_client()) {
                customerID = order.get_client().id;
            }
            this.state.promotion_id = false
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
                    model: 'promotion.voucher.line',
                    method: 'check_promotion',
                    args: args,
                }).then((response) => {
                    if ('promotion_id' in response) {
                        this.state.promotion_id = response['promotion_id']
                    }
                });
            }
            return this.state.promotion_id
        }

        async get_promotion_id() {
            let payload = this.getPayload()
            var customerID = false;
            const order = this.props.order;
            if (order.get_client()) {
                customerID = order.get_client().id;
            }
            this.state.promotion_id = false
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
                    model: 'promotion.voucher.line',
                    method: 'check_promotion',
                    args: args,
                }).then((response) => {
                    if ('get_promotion_id' in response) {
                        this.state.promotion_id = response['get_promotion_id']
                    }
                });
            }
            return this.state.promotion_id
        }

        async get_promotion_code() {
            let payload = this.getPayload()
            var customerID = false;
            const order = this.props.order;
            if (order.get_client()) {
                customerID = order.get_client().id;
            }
            this.state.promotion_id = false
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
                    model: 'promotion.voucher.line',
                    method: 'check_promotion',
                    args: args,
                }).then((response) => {
                    if ('code_promotion' in response) {
                        this.state.promotion_id = response['code_promotion']
                    }
                });
            }
            return this.state.promotion_id
        }

        async onClickButtonPromotionVoucher(ev) {
            let payload = this.getPayload()
            var customerID = false;
            const order = this.props.order;
            if (order.get_client()) {
                customerID = order.get_client().id;
            }
            this.state.message = undefined;
            if (payload['newArray'].length > 0) {
                let id = payload['newArray'][0]['_id']
                let name = payload['newArray'][0]['text']
                let args = [id, name, customerID];
                var message = false;
                var ifConnected = window.navigator.onLine;
                if (!ifConnected) {
                    this.state.message = '* Đường truyền mạng có vấn đề. Vui lòng kiểm tra lại!';
                    this.playSound('error');
                }
                const result = await this.rpc({
                    model: 'promotion.voucher.line',
                    method: 'check_promotion',
                    args: args,
                }).then((response) => {
                    if ('message' in response) {
                        // message = response['message'];
                        this.state.message = '* ' + response['message'];
                        this.playSound('error');
                    }
                });

            } else {
                this.state.message = '* Xin vui lòng nhập mã khuyến mại!'
                this.playSound('error');
            }
            // Sau khi check các trường hợp không hợp lệ thực hiện tiếp
            if (this.state.message == undefined) {
                await this.confirm()
            }
        }
    }

    VoucherPromotionPopup.template = 'VoucherPromotionPopup';
    VoucherPromotionPopup.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        array: [],
        isSingleItem: false,
    };

    Registries.Component.add(VoucherPromotionPopup);

    return VoucherPromotionPopup;
});
