odoo.define('ev_promotion_voucher.PromotionVoucherProductScreen', function (require) {
    "use strict"
    const core = require('web.core');
    // const ProductScreen = require('point_of_sale.ProductScreen');
    const ProductScreen = require('ev_pos_promotion.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    const {useState} = owl.hooks;
    const _t = core._t;
    const rpc = require('web.rpc');
    let PromotionVoucherProductScreen = ProductScreen =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                this.generatePromotions();
                this.handleOnClickApplyPromotionCode = this.handleOnClickApplyPromotionCode.bind(this);
                // this.handleOnClickButtonPromotionVoucher = this.handleOnClickButtonPromotionVoucher.bind(this);
            }

            //hàm cập nhật CTKM trên POS gọi callback tới pos_promotion
            handleOnClickApplyPromotionCode(ev) {
                this.generatePromotions();
            }

            async _updateSelectedOrderline(event) {
                const order_before = this.currentOrder;
                var promotion_code = []
                var promotion_id = []
                const order = this.currentOrder;
                order_before.orderlines.forEach((line) => {
                    if (line.promotion_code && line.promotion_id) {
                        // promotion_code = line.promotion_code;
                        promotion_code.push(line.promotion_code)
                        promotion_id.push(line.promotion_id)
                    }
                });
                // promotion_code.forEach((code) => {
                //     let args_code = [order.name, order.name, code];
                //     this.rpc({
                //         model: 'promotion.voucher.count',
                //         method: 'delete_promotion_code_used',
                //         args: args_code,
                //     });
                // })
                super._updateSelectedOrderline(event);
                this.env.pos.removePromotionsApplied();
                this.generatePromotions();
            }

            handleOnClickSelect(ev, promotions) {
                const order_before = this.currentOrder;
                var promotion_code = []
                var promotion_id = []
                const order = this.currentOrder;
                order_before.orderlines.forEach((line) => {
                    if (line.promotion_code && line.promotion_id) {
                        // promotion_code = line.promotion_code;
                        promotion_code.push(line.promotion_code)
                        promotion_id.push(line.promotion_id)
                        promotion_code.forEach((code) => {
                            let args_code = [order.name, order.name, code];
                            this.rpc({
                                model: 'promotion.voucher.count',
                                method: 'delete_promotion_code_used',
                                args: args_code,
                            });
                        })
                    }
                });
                // super.handleOnClickSelect(ev, promotions);
                let appliedPromotions = [];
                // ${1}
                let selectedPromIds = promotions.map((item) => {
                    return item.id;
                });
                this.state.promotions.forEach((item) => {
                    let select = _.indexOf(selectedPromIds, item.id) != -1;
                    item.setSelect(select);
                    if (item.selected)
                        appliedPromotions.push(item);
                });
                // ${2}
                this.env.pos.removePromotionsApplied();
                // ${3}
                this.env.pos.applyPromotions(appliedPromotions);
                // ${4}
                this.generatePromotions();
                // ${5}
                this.generatePromotions_after_use_promotion()

            }

            // hàm cập nhật lại dòng KM ở ngay dưới SP được KM
            generatePromotions_after_use_promotion() {
                const order = this.currentOrder;
                let arr_orderline = []
                let arr_orderline_promotion = []
                let arr_orderline_not_promotion = []
                let arr_orderline_concat = []

                let orderline = order.get_orderlines()
                orderline.forEach((line) => {
                    arr_orderline.push(line)
                })
                //xóa line trong orderline
                var order_test = this.env.pos.get_order();

                for (var lines in order.get_orderlines()) {
                    order_test.remove_orderline(order.get_orderlines());
                }
                arr_orderline.forEach((line) => {
                    if (line.x_sequence) {
                        //thêm các sản phẩm áp dụng CTKM và KM
                        arr_orderline_promotion.push(line)
                    } else {
                        //thêm các sản phẩm ko áp dụng CTKM và KM
                        arr_orderline_not_promotion.push(line)
                    }
                })
                // sắp xếp lại phần tử trên orderline với x_sequence
                for (let i = 0; i < arr_orderline_promotion.length - 1; i++) {
                    for (let j = i + 1; j < arr_orderline_promotion.length; j++) {
                        if (arr_orderline_promotion[j].x_sequence < arr_orderline_promotion[i].x_sequence) {
                            let t = arr_orderline_promotion[i];
                            arr_orderline_promotion[i] = arr_orderline_promotion[j];
                            arr_orderline_promotion[j] = t;
                        }
                    }
                }
                //kiểm tra phần tử trùng nhua và đưa lên đầu tiên
                var valuesSoFar = [];
                let value_line_same = [];
                let value_line_not_same = [];
                let value_line_not_same_line = [];
                for (var i = 0; i < arr_orderline_promotion.length; ++i) {
                    var value = arr_orderline_promotion[i].x_sequence;
                    if (valuesSoFar.indexOf(value) !== -1) {
                        value_line_same.push(value)
                    }
                    valuesSoFar.push(value);
                }
                //lấy phần tử k trùng sequence trong orderline
                arr_orderline_promotion.forEach((line) => {
                    if (!value_line_same.includes(line.x_sequence)) {
                        value_line_not_same.push(line.x_sequence)
                        value_line_not_same_line.push(line)
                    }
                })
                let arr_not_same_remove_first = []
                arr_orderline_promotion.forEach((line) => {
                    if (value_line_not_same.indexOf(line.x_sequence) === -1) {
                        arr_not_same_remove_first.push(line)
                    }
                })
                // chuyển các SP KH ko có sequence (chỉ có 1 mình ) xuống dưới cùng,
                let arr_last = arr_not_same_remove_first.concat(value_line_not_same_line)
                arr_orderline_concat = arr_orderline_promotion.concat(arr_orderline_not_promotion)
                //gộp các chuỗi đã sắp xếp
                let arr_last_sum = arr_last.concat(arr_orderline_not_promotion)

                //xử lý trùng sequence_promotion, sắp xếp lại theo sequence_promotion
                for (let i = 0; i < arr_last_sum.length - 1; i++) {
                    for (let j = i + 1; j < arr_last_sum.length; j++) {
                        if (arr_last_sum[j].sequence_promotion < arr_last_sum[i].sequence_promotion) {
                            let t = arr_last_sum[i];
                            arr_last_sum[i] = arr_last_sum[j];
                            arr_last_sum[j] = t;
                        }
                    }
                }
                //sắp xếp lại line theo promotion_id (sp được KM trước KM)
                for (let i = 0; i < arr_last_sum.length - 1; i++) {
                    for (let j = i + 1; j < arr_last_sum.length; j++) {
                        if (arr_last_sum[j].promotion_id === undefined && arr_last_sum[i].promotion_id && arr_last_sum[j].sequence_promotion === arr_last_sum[i].sequence_promotion) {
                            let t = arr_last_sum[i];
                            arr_last_sum[i] = arr_last_sum[j];
                            arr_last_sum[j] = t;
                        }
                    }
                }

                arr_last_sum.forEach((line) => {
                    order_test.add_orderline(line);
                })
            }


            // hàm phân bổ CTKM nếu có điểm tích lũy, CTKM giảm giá theo tổng giá trị đơn hàng
            allocate_total() {
                let order = this.currentOrder;
                let orderline = order.get_orderlines();
                //Xóa phân bổ rồi tính lại
                for(var i = 0; i < orderline.length; i++){
                    var line = orderline[i];
                    if(typeof line.amount_promotion_total != undefined){
                        line.amount_promotion_total = 0;
                    }
                    if(typeof line.amount_promotion_loyalty != undefined){
                        line.amount_promotion_loyalty = 0;
                    }
                }

                let lines = order.orderlines.filter((item) => {
                    return item.price > 0 && item.discount != 100;
                });
                let total_price_allocate = 0;
                let total_price_allocate_reward = 0;
                //tính tổng giá trị đơn hàng các sản phẩm không phải KM
                let sum_price_product_before = 0;
                lines.forEach((line) => {
                    var p_amount = 0;
                    if(line.x_is_price_promotion !== undefined){
                        p_amount = parseInt(line.x_is_price_promotion);
                    }
                    if(line.discount < 100){
                        sum_price_product_before += (line.price * line.quantity) - p_amount;
                    }
                })

                order.orderlines.forEach((line_loyalty) => {
                    if (line_loyalty.reward_custom_id === "reward") {
                        total_price_allocate_reward += line_loyalty.price * -1
                    }
                    if (line_loyalty.type === 'total_amount') {
                        total_price_allocate += line_loyalty.price * -1
                    }
                })

                if (total_price_allocate > 0 || total_price_allocate_reward > 0) {
                    var total_discount_allocate = 0;
                    var total_discount_allocate_reward = 0;
                    var count = 0;
                    var length = lines.length;
                    var amount_promotion_total = 0;
                    var i = 0
                    lines.forEach((line) => {
                        count = count + 1;
                        var promotion_amount = 0;
                        if(line.x_is_price_promotion !== undefined){
                            promotion_amount = parseInt(line.x_is_price_promotion);
                        }
                        var discount = Math.ceil((((line.price * line.quantity) - promotion_amount) * 100) / sum_price_product_before);
                        if (total_price_allocate > 0) {
                            var total_discount = Math.round(total_price_allocate * (discount / 100))
                            if (total_discount > 0) {
                                let price_subtotal_incl = line.get_price_with_tax()
                                if (count < length) {
                                    var max_price_discount_allowed =  price_subtotal_incl - promotion_amount;
                                    if (total_discount > max_price_discount_allowed) {
                                        total_discount = max_price_discount_allowed
                                    }
                                    // Cộng tổng số tiền đã phân bổ
                                    total_discount_allocate = Math.round(total_discount_allocate + total_discount)

                                    if (total_discount_allocate <= total_price_allocate) {
                                        i = count
                                        amount_promotion_total = total_discount;
                                        line.setAmountPromotionTotal(total_discount)
                                    } else {
                                        i = count
                                        amount_promotion_total = total_price_allocate - (total_discount_allocate - total_discount);
                                        line.setAmountPromotionTotal(amount_promotion_total)
                                        total_discount_allocate = total_price_allocate
                                    }
                                }
                                if (count === length) {
                                    i = count
                                    amount_promotion_total = total_price_allocate - total_discount_allocate;
                                    line.setAmountPromotionTotal(amount_promotion_total)
                                }
                            } else {
                                if (total_discount_allocate < total_price_allocate && count == length) {
                                    let tmp_discount = total_price_allocate - total_discount_allocate
                                    lines[i - 1].setAmountPromotionTotal(lines[i - 1].amount_promotion_total + tmp_discount)
                                }
                            }

                            // if (count == length && total_discount_allocate < total_price_allocate) {
                            //     var tmp_discount = total_price_allocate - (total_discount_allocate - total_discount)
                            //     if (tmp_discount > 0)
                            //         lines[count - 2].setAmountPromotionTotal(tmp_discount + lines[count - 2].amount_promotion_total)
                            // }


                            // if(total_discount_allocate < total_price_allocate && count < length){
                            //     line.setAmountPromotionTotal(total_discount);
                            // } else{
                            //     var tmp_discount = total_price_allocate - (total_discount_allocate - total_discount);
                            //     if(tmp_discount > 0){
                            //         line.setAmountPromotionTotal(tmp_discount);
                            //     }
                            // }
                        }

                        if(total_price_allocate_reward > 0){
                            var max_discount_reward_allowed = line.get_price_with_tax() - promotion_amount - amount_promotion_total;
                            if (max_discount_reward_allowed < 0){
                                max_discount_reward_allowed = 0;
                            }
                            var total_discount_reward = Math.ceil(total_price_allocate_reward * (discount/100));
                            if (total_discount_reward > max_discount_reward_allowed){
                                total_discount_reward = max_discount_reward_allowed;
                            }
                            total_discount_allocate_reward = Math.ceil(total_discount_allocate_reward + total_discount_reward);
                            if(total_discount_allocate_reward < total_price_allocate_reward && count < length){
                                line.setAmountPromotionLoyalty(total_discount_reward);
                            } else{
                                var tmp_discount = total_price_allocate_reward - (total_discount_allocate_reward - total_discount_reward);
                                if(tmp_discount > 0) {
                                    line.setAmountPromotionLoyalty(tmp_discount);
                                }
                            }
                        }

                    })
                }
                order.orderlines.forEach((line_total_amount) => {
                    if (line_total_amount.type === 'total_amount') {
                        lines.forEach((line) => {
                            if (line.x_product_promotion === undefined) {
                                line.setProductPromotion(line_total_amount.x_product_promotion)
                            } else {
                                let arr = line.x_product_promotion.split(',')
                                if (!arr.includes(' ' + line_total_amount.x_product_promotion)) {
                                    line.setProductPromotion(line.x_product_promotion + ', ' + line_total_amount.x_product_promotion)
                                } else {
                                    return
                                }
                            }
                        })
                    }
                });

                //Phân bổ một sản phẩm 2 chương trình
                for(var i = 0; i < orderline.length; i++){
                    var line = orderline[i];
                    if(line.x_is_price_promotion != undefined && line.x_is_price_promotion != ''){
                        var amount_promotion = parseInt(line.x_is_price_promotion);
                        if(amount_promotion > 0){
//                            console.log(amount_promotion);
                            var total_amount_promotion = 0;
                            var count_promotion = 0;
                            for(var j = 0; j < orderline.length; j++){
                                var line2 = orderline[j];
                                if(line2.sequence_promotion != undefined && line2.sequence_promotion == line.id && line2.id != line.id){
                                    total_amount_promotion += Math.abs(line2.price);
                                    count_promotion ++;
                                }
                            }
                            if(total_amount_promotion > amount_promotion && count_promotion > 1){
                                line.x_is_price_promotion = total_amount_promotion;
                            }
                        }
                    }
//                    console.log(line);
                }

            }


            handleOnClickSelectAll(ev, promotions) {
                const order_before = this.currentOrder;
                var promotion_code = []
                var promotion_id = []
                const order = this.currentOrder;
                order_before.orderlines.forEach((line) => {
                    if (line.promotion_code && line.promotion_id) {
                        // promotion_code = line.promotion_code;
                        promotion_code.push(line.promotion_code)
                        promotion_id.push(line.promotion_id)
                        promotion_code.forEach((code) => {
                            let args_code = [order.name, order.name, code];
                            this.rpc({
                                model: 'promotion.voucher.count',
                                method: 'delete_promotion_code_used',
                                args: args_code,
                            });
                        })
                    }
                });
                // bỏ kế thừa
                // super.handleOnClickSelectAll(ev, promotions);
                // ${1}
                this.state.promotions.forEach((item) => {
                    item.setSelect(true);
                });
                // ${2}
                this.env.pos.removePromotionsApplied();
                // ${3}
                this.env.pos.applyPromotions(promotions);
                // ${4}
                this.generatePromotions();
                // ${5}
                this.generatePromotions_after_use_promotion()
            }

            // @param {} ev
            handleOnClickClearPromotionButton(ev) {
                const order_before = this.currentOrder;
                var promotion_code = []
                var promotion_id = []
                const order = this.currentOrder;
                order_before.orderlines.forEach((line) => {
                    if (line.promotion_code && line.promotion_id) {
                        promotion_code.push(line.promotion_code)
                        promotion_id.push(line.promotion_id)
                        promotion_code.forEach((code) => {
                            let args_code = [order.name, order.name, code];
                            this.rpc({
                                model: 'promotion.voucher.count',
                                method: 'delete_promotion_code_used',
                                args: args_code,
                            });
                        })
                    }
                });
                // xóa giá phân bổ khi xóa CTKM
                order.orderlines.forEach((line) => {
                    line.x_is_price_promotion = undefined
                    line.x_product_promotion = undefined
                })
                this.env.pos.removePromotionsApplied();
                this.generatePromotions();
            }

            get client() {
                return super.client;
            }

            async _clickProduct(event) {
                this.env.pos.setPromotionAllocateNone();
                const order_before = this.currentOrder;
                const order = this.currentOrder;
                var promotion_code;
                var promotion_id;
                order_before.orderlines.forEach((line) => {
                    if (line.promotion_code && line.promotion_id) {
                        promotion_code = line.promotion_code;
                        promotion_id = line.promotion_id;
                    }
                });
                order_before.orderlines.forEach((line) => {
                    if(typeof line !== 'undefined'){
                        if(typeof line.reward_custom_id !== 'undefined'){
                            if (line.reward_custom_id === "reward"){
                                order_before.remove_orderline(line);
                            }
                        }
                    }
                });
                let promotion_code_arr = []
                let promotion_id_arr = []
                order_before.orderlines.forEach((line) => {
                    if (line.promotion_code && line.promotion_id) {
                        promotion_code_arr.push(line.promotion_code)
                        promotion_id_arr.push(line.promotion_id)
                        // promotion_code_arr.forEach((code) => {
                        //     let args_code = [order.name, order.name, code];
                        //     this.rpc({
                        //         model: 'promotion.voucher.count',
                        //         method: 'delete_promotion_code_used',
                        //         args: args_code,
                        //     });
                        // })
                    }
                });
                // let args = [promotion_id, promotion_code];
                // this.rpc({
                //     model: 'promotion.voucher.line',
                //     method: 'update_promotion_used_return',
                //     args: args,
                // });
                super._clickProduct(event);
                this.env.pos.removePromotionsApplied();
                this.generatePromotions();
            }
        };
    Registries.Component.extend(ProductScreen, PromotionVoucherProductScreen);

    return ProductScreen;
});