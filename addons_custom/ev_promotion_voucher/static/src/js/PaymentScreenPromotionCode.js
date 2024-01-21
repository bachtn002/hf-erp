odoo.define('ev_promotion_voucher.PaymentScreenPromotionCode', function (require) {
    "use strict"

    const core = require('web.core');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const PosModel = require('point_of_sale.models');
    var utils = require('web.utils');
    var round_pr = utils.round_precision;


    const {useState} = owl.hooks;

    const _t = core._t;
    let PaymentScreenPromotionCode = PaymentScreen =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
            }

            // async validateOrder_super(isForceValidate) {
            //     if (await this._isOrderValid(isForceValidate)) {
            //         // remove pending payments before finalizing the validation
            //         for (let line of this.paymentLines) {
            //             if (!line.is_done()) this.currentOrder.remove_paymentline(line);
            //         }
            //         await this._finalizeValidation();
            //         const order = this.currentOrder;
            //         let promotion_code;
            //         let promotion_id;
            //         order.orderlines.forEach((line) => {
            //             if (line.promotion_code) {
            //                 promotion_code = line.promotion_code;
            //                 promotion_id = line.promotion_id;
            //             }
            //         });
            //         // let args_code = [order.name, order.name, promotion_code];
            //         // this.rpc({
            //         //     model: 'pos.order',
            //         //     method: 'update_status',
            //         //     args: args_code,
            //         // });
            //
            //     }
            //     else {
            //         await this.showPopup('ErrorPopup', {
            //             title: 'Error: no internet connection.',
            //             // body: error,
            //         });
            //     }
            // }


            async _finalizeValidation() {
                var result = await super._finalizeValidation();
                if (result != false){
                    var promotion_code = [];
                    const order = this.currentOrder;
                    order.orderlines.forEach((line) => {
                        if (line.promotion_code) {
                            promotion_code.push(line.promotion_code)
                        }
                    });
                    // loại bỏ promotion code trùng nhau😃
                    var promotion_code_not_same = [];
                    promotion_code.forEach((code_promotion)=>{
                        if (_.indexOf(promotion_code_not_same, code_promotion) === -1) {
                            promotion_code_not_same.push(code_promotion)
                        }
                    })
                    var orderlines = order.get_orderlines();
                    for(var i = 0; i < orderlines.length; i++){
                        var line = orderlines[i];
                        if(line.quantity == 0){
                            return false;
                        }
                    }
                    let customerID = false
                    if (order.get_client()){
                        customerID = order.get_client().id
                    }
                    //Không sử dụng hàm update_promotion_used để update code_promotion nữa
                    // promotion_code_not_same.forEach((code_promotion) => {
                    //     let args_code = [order.name, order.name, code_promotion, customerID];
                    //     this.rpc({
                    //         model: 'promotion.voucher.count',
                    //         method: 'update_promotion_used',
                    //         args: args_code,
                    //     });
                    // });
                }

            }
            async validateOrder(isForceValidate) {
                const order = this.currentOrder;
                const paymentlines = order.paymentlines;
                let payment_amount = 0
                paymentlines.forEach((line)=>{
                    payment_amount+= line.get_amount()
                })
                if (paymentlines.length > 0 && payment_amount >= order.get_total_with_tax()) {
                    var promotion_code = [];
                    var promotion_id = []
                    order.orderlines.forEach((line) => {
                        if (line.promotion_code) {
                            promotion_code.push(line.promotion_code)
                        }
                    });
                    let check_error = []
                    let customerID = false
                    if (order.get_client()){
                        customerID = order.get_client().id
                    }
                    for (const code_promotion of promotion_code) {
                        let result = await this.rpc({
                            model: 'promotion.voucher.count',
                            method: 'check_promotion_code',
                            args: [order.name, order.name, code_promotion, customerID],
                        }).then((response) => {
                            if ('message' in response) {
                                check_error.push(response)
                            }
                        });
                    }
                    if (check_error.length > 0) {
                        this.showPopup('ErrorPopup', {
                            title: _('Mã promotion code đã được sử dụng'),
                        });
                        return false;
                    }
                    if (check_error.length === 0) {
//                        promotion_code.forEach((code_promotion) => {
//                            let args_code = [order.name, order.name, code_promotion];
//                            this.rpc({
//                                model: 'promotion.voucher.count',
//                                method: 'update_promotion_used',
//                                args: args_code,
//                            });
//                        });
                        super.validateOrder(isForceValidate);
                    }
                }
            }
        }
    Registries.Component.extend(PaymentScreen, PaymentScreenPromotionCode);

    return PaymentScreen;
});