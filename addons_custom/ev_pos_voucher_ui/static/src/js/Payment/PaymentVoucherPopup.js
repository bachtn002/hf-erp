odoo.define('ev_pos_voucher_ui.PaymentVoucherPopup', function (require) {
    'use strict';

    const {useState} = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const {useAutoFocusToLast} = require('point_of_sale.custom_hooks');

    class PaymentVoucherPopup extends AbstractAwaitablePopup {
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

        async confirm() {
            var products = [];
            var payments = [];
            const order = this.props.order;
            var amount_total = order.get_total_with_tax();
            var amount_due = order.get_due();
            var customerID = false
            var config_id = this.env.pos.config.id
            var promotion = false
            if (order.get_client()) {
                customerID = order.get_client().id;
            }
            const orderlines = order.orderlines;
            const paymentlines = order.paymentlines;
            orderlines.forEach((line) => {
                products.push(
                    {
                        product_id: line.product.id,
                        quantity: line.quantity,
                        price: line.price * line.quantity,
                    }
                );
                if (line.promotion_id) {
                    promotion = true
                }
                ;
            });
            paymentlines.forEach((line) => {
                if (line.payment_method.x_is_voucher == true) {
                    payments.push(
                        {
                            lot_name: line.lot_name,
                            amount: line.amount,
                        }
                    );
                }
            });
            let payload = await this.getPayload();
            if (payload['newArray'].length > 0) {
                let lot_name = payload.newArray[0].text;
                let id = payload.newArray[0]._id
                let args = [id, lot_name, products, customerID, payments, amount_total, amount_due, config_id, promotion];
                var amount = 0
                var ifConnected = window.navigator.onLine;
                if (!ifConnected) {
                    this.state.message = '* Đường truyền mạng có vấn đề. Vui lòng kiểm tra lại!';
                    this.playSound('error');
                }
                await this.rpc({
                    model: 'stock.production.lot',
                    method: 'check_code_payment_from_ui',
                    args: args,
                }).then((response) => {
                    // console.log('test', response)
                    if ('message' in response) {
                        this.state.message = '* ' + response['message'];
                        this.playSound('error');
                    } else {
                        amount += response['amount'];
                        payload.amount = amount;
                        this.props.resolve({confirmed: true, payload: payload});
                        this.trigger('close-popup');
                    }
                });
            } else {
                this.state.message = '* Xin vui lòng nhập mã voucher!';
                this.playSound('error');
            }
        }
    }

    PaymentVoucherPopup.template = 'PaymentVoucherPopup';
    PaymentVoucherPopup.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        array: [],
        isSingleItem: false,
    };

    Registries.Component.add(PaymentVoucherPopup);

    return PaymentVoucherPopup;
})
;
