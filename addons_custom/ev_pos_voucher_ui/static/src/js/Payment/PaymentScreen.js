odoo.define('ev_pos_voucher_ui.PaymentScreen', function (require) {
    "use strict"

    const core = require('web.core');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const PosModel = require('point_of_sale.models');
    var utils = require('web.utils');
    var round_pr = utils.round_precision;


    const {useState} = owl.hooks;

    const _t = core._t;


    let VoucherPaymentScreen = PaymentScreen =>
        class extends PaymentScreen {

            /**
             * [Inheritant] constructor.
             */
            constructor() {
                super(...arguments);
                this.addPaymentVoucher = this.addPaymentVoucher.bind(this);
                this.check_click = 0;
            }

            async back_custom(event) {
                if(this.back_screen){
                    const order = this.currentOrder;
                    const paymentlines = order.paymentlines;
                    paymentlines.forEach((line) => {
                        if (typeof line.lot_name !== 'undefined') {
                            let lot_name = line.lot_name
                            let args = [lot_name, lot_name];
                            this.rpc({
                                model: 'stock.production.lot',
                                method: 'update_voucher_status_after_delete',
                                args: args,
                            })
                        }
                    })
                    // xóa voucher khi bấm quay lại ở màn hình thanh toán
                    var remove_payment = []
                    paymentlines.forEach((line) => {
                        // if (line.lot_name) {
                        //     remove_payment.push(line)
                        // }
                        remove_payment.push(line)
                    });
                    remove_payment.forEach((line) => {
                        order.remove_paymentline(line)
                    });
                    this.showScreen('ProductScreen');
                } else {
                    await this.showPopup('ErrorPopup', {
                        title: 'Thông báo',
                        body: 'Đơn hàng đang thực hiện đẩy lên hệ thống. Bạn không thể quay lại tại thời điểm này.',
                    });
                }
            }

            /**
             * []ADD addPaymentVoucher.
             *
             * Them 1 dong thanh toan bang VC/CP
             *
             */
            addPaymentVoucher(order, amount, paymentMethod, lot_name) {
                var newPaymentline = new PosModel.Paymentline({}, {
                    order: order,
                    payment_method: paymentMethod,
                    pos: order.pos
                });
                newPaymentline.set_amount(round_pr(amount, order.pos.currency.rounding));
                newPaymentline.lot_name = lot_name;
                order.paymentlines.add(newPaymentline);
                order.select_paymentline(newPaymentline);
                return newPaymentline;
            }

            /**
             * []Inheritant addNewPaymentLine.
             *
             * Hiển thị popup nhap ma VC/CP
             *
             */
            async addNewPaymentLine({detail: paymentMethod}) {
                const order = this.currentOrder;
                const paymentlines = order.paymentlines;
                var check_payment_by_voucher = false;
                paymentlines.forEach((line) => {
                    if (line.payment_method.x_is_voucher == true) {
                        check_payment_by_voucher = true;
                    }
                });
                if (paymentMethod.x_is_voucher == true) {
                    const {confirmed, payload} = await this.showPopup('PaymentVoucherPopup', {
                        title: this.env._t('Vui lòng nhập mã phiếu mua hàng để thanh toán!'),
                        order: order
                    });
                    if (confirmed) {
                        // cập nhật trạng thái phiếu voucher khi sử dụng
                        let lot_name = payload.newArray[0].text;
                        let id = payload.newArray[0]._id
                        let args = [id, lot_name]
                        // HungPT không thay đổi trạng thái khi nhập voucher
                        // await this.rpc({
                        //     model: 'stock.production.lot',
                        //     method: 'update_voucher_status_after_used',
                        //     args: args,
                        // })
                        this.addPaymentVoucher(order, payload.amount, paymentMethod, payload.newArray[0].text);
                        return true
                    } else {
                        // We don't proceed on adding product.
                        return true;
                    }
                } else {
                    // if (check_payment_by_voucher) {
                    //     this.showPopup('ErrorPopup', {
                    //         title: this.env._t('Payment Invalid'),
                    //         body: this.env._t(
                    //             'Vui lòng kiểm tra thông tin thanh toán (Phiếu mua hàng phải thanh toán sau cùng).'
                    //         ),
                    //     });
                    //     return true;
                    // }
                    super.addNewPaymentLine({detail: paymentMethod});
                }
            }

            async _updateSelectedPaymentline() {
                if (this.selectedPaymentLine && this.selectedPaymentLine.payment_method.x_is_voucher == true) {
                    return;
                } else {
                    super._updateSelectedPaymentline();
                }
            }

            async validateOrder(isForceValidate) {
                const order = this.currentOrder;
                const orderlines = order.orderlines;
                const paymentlines = order.paymentlines;
                var config_id = this.env.pos.config.id
                var list_voucher_to_sale = [];
                var list_voucher_to_payment = [];  //danh sách các voucher sử dụng
                var check_amount_bank_than = []
                var amount_check = 0
                var promotion = false
                orderlines.forEach((line) => {
                    if (line.has_product_lot == true) {
                        line.pack_lot_lines.forEach((lot) => {
                            list_voucher_to_sale.push(lot.attributes.lot_name);
                        });
                    }
                    if (line.promotion_id) {
                        promotion = true
                    }
                });
                paymentlines.forEach((line) => {
                    if (line.payment_method.x_is_voucher == true) {
                        list_voucher_to_payment.push(line.lot_name);
                    }
                    console.log(line);
                    // if (!line.payment_method.is_cash_count && line.amount > order.get_total_with_tax()) {
                    if (!line.payment_method.is_cash_count && line.amount > order.get_total_with_tax() - amount_check) {
                        check_amount_bank_than.push(line);
                    }

                    if(line.amount < 0){
                        check_amount_bank_than.push(line);
                    }
                    amount_check += line.amount

                });
                var customerID = false
                if (order.get_client()) {
                    customerID = order.get_client().id;
                }
                var message = false;
                // const orderId = order.backendId;


                if (check_amount_bank_than.length > 0) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Lỗi'),
                        body: this.env._t('Đối với phương thức thanh toán khác tiền mặt, số tiền phải nhỏ hơn hoặc bằng tổng giá trị đơn hàng. Tất cả các phương thức không được nhỏ hơn 0.'),
                    });
                    return
                }

                if (list_voucher_to_payment.length > 0) {
                    let args = [[false], list_voucher_to_payment, customerID, config_id, promotion];
                    await this.rpc({
                        model: 'stock.production.lot',
                        method: 'check_code_from_ui_validate_if_modify',
                        args: args,
                    }).then((response) => {
                        if ('message' in response) {
                            message = response['message'];
                        }
                    });
                    if (message) {
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Mã voucher không hợp lệ'),
                            body: this.env._t(
                                message
                            ),
                        });
                        return false;
                    } else {
                        // SangNT comment code duplicate update voucher with _update_infor_voucher_user
                        // if(this.check_click == 0){
                        //     list_voucher_to_payment.forEach((lot_name) => {
                        //         let args = [lot_name, lot_name]
                        //         this.rpc({
                        //             model: 'stock.production.lot',
                        //             method: 'update_voucher_status_after_used',
                        //             args: args,
                        //         })
                        //     });
                        //     this.check_click = this.check_click + 1;
                        // }
                        super.validateOrder(isForceValidate);
                    }
                } else {
                    super.validateOrder(isForceValidate);
                }
                // if (list_voucher_to_payment.length > 0 || list_voucher_to_payment.length > 0) {
                //     let args = [[false], list_voucher_to_sale, list_voucher_to_payment, customerID, config_id];
                //     await this.rpc({
                //         model: 'stock.production.lot',
                //         method: 'check_code_from_ui_validate',
                //         args: args,
                //     }).then((response) => {
                //         if ('message' in response) {
                //             message = response['message'];
                //         }
                //     });
                //     if (message) {
                //         this.showPopup('ErrorPopup', {
                //             title: this.env._t('Voucher Invalid'),
                //             body: this.env._t(
                //                 message
                //             ),
                //         });
                //         return false;
                //     }
                //     super.validateOrder(isForceValidate);
                // }
                // else {
                //     super.validateOrder(isForceValidate);
                // }

            }

            deletePaymentLine(event) {
                const {cid} = event.detail;
                const line = this.paymentLines.find((line) => line.cid === cid);
                if (typeof line.lot_name !== 'undefined') {
                    let lot_name = line.lot_name
                    let args = [lot_name, lot_name];
                    // this.rpc({
                    //     model: 'stock.production.lot',
                    //     method: 'update_voucher_status_after_delete',
                    //     args: args,
                    // })
                }
                super.deletePaymentLine(event)
            }

        };

    Registries.Component.extend(PaymentScreen, VoucherPaymentScreen);

    return PaymentScreen;

});
