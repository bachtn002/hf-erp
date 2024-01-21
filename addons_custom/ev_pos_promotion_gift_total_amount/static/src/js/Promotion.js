odoo.define('ev_pos_promotion_gift_total_amount.Promotion', function (require) {
    "use strict"

    const models = require('ev_pos_promotion.Promotion');
    const Promotion = models.Promotion;
    const rpc = require('web.rpc');
    const PosComponent = require('point_of_sale.PosComponent');
    models.Promotion = Promotion.extend({
        initFromJson: function (json) {
            Promotion.prototype.initFromJson(json);
            this.pos_promotion_gift_total_amount_ids = json.pos_promotion_gift_total_amount_ids;
        },
        exportToJson: function () {
            let json = Promotion.prototype.exportToJson();
            json.pos_promotion_gift_total_amount_ids = this.pos_promotion_gift_total_amount_ids;
            return json;
        },
        // isValidOrder: async function (order, show) {
        isValidOrder: function (order, show) {
            let res = Promotion.prototype.isValidOrder.call(this, order, show);
            let args = [this.id, this.id];
            if (this.type !== 'gift_total_amount') {
                return res;
            }
            // check in time
            let isValidTime = this.isValidTime()
            if (!isValidTime) {
                return res
            }
            // check partner for not apply promotion
            let isValidPartnerNot = this.isValidPartnerNot(order);
            if (!isValidPartnerNot) {
                return res
            }
            // check partner for apply promotion
            let isValidPartner = this.isValidPartner(order)
            if (!isValidPartner) {
                return res
            }

            let conditions = this.db.getPromotionGiftTotolAmountByPromotionIds([this.id]);
            if (conditions.length < 1) {
                return false;
            }
            let amount_min = 0;
            var lowest = Number.POSITIVE_INFINITY;
            var tmp;
            conditions.forEach((item) => {
                tmp = item.total_amount;
                if (tmp < lowest) lowest = tmp;
            });
            // Kiêm tra giá trị đơn hàng có lớn hơn giá trị điều kiện không,
            // Nếu không có giá trị thì thông tính
            let arr = []
            conditions.forEach((condition) => {
                arr.push(condition.total_amount)
                // this.CheckProductInPos(order, condition)
            });
            let test = [];
            arr.forEach((ar) => {
                if (order.get_total_with_tax() > ar) {
                    test = [];
                    test.push(ar)
                }
            });
            var check;  //kiểm tra nế sp gộp thì k hiện chương trình khuyến mại
            conditions.forEach((condition) => {
                if (condition.total_amount === test[0]) {
                    check = this.CheckApplyType(order, condition);
                }
            });

            this.getPricePromotion(order, conditions);
            if (order.get_total_with_tax() <= lowest && lowest !== 0) {
                return false;
            } else if (check) {
                return false
            }
            return true
        },
        getPricePromotion(order, conditions) {
            let dict_product = {};
            let dict_product_order = {};
            conditions.forEach((condition) => {
                let product_ids = condition.product_id
                product_ids.forEach((product_id) => {
                    dict_product[product_id] = condition.qty
                })
            });
            order.orderlines.forEach((line) => {
                dict_product_order[line.product.id] = line.quantity
            });
        },
        applyPromotionToOrder: function (order) {
            Promotion.prototype.applyPromotionToOrder.call(this, order);
            if (this.type !== 'gift_total_amount') {
                return;
            }
            if (!this.isValidOrder(order)) {
                return;
            }
            let conditions = this.db.getPromotionGiftTotolAmountByPromotionIds([this.id])  //lấy danh sách sp thêm
            let arr = [];
            conditions.forEach((condition) => {
                arr.push(condition.total_amount)
            });

            // lấy ra condittion ứng với giá lớn nhất
            let arr_condition_apply = [];
            arr.forEach((ar) => {
                if (order.get_total_with_tax() > ar) {
                    arr_condition_apply = []
                    arr_condition_apply.push(ar)
                }
            });

            conditions.forEach((condition) => {
                arr_condition_apply.forEach((te) => {
                    if (condition.total_amount === te) {
                        this.CheckProductInPos(order, condition)
                    }
                })
            });
        },
        /**
         * @return {boolean}
         */
        CheckApplyType: function (order, condition) {
            let product_in_condition = [];
            condition.product_id.forEach((pr) => {
                product_in_condition.push(pr)
            });
            let arr = [];
            order.orderlines.forEach((line) => {
                if (_.indexOf(product_in_condition, line.product.id) !== -1 && line.quantity >= condition.qty) {
                    arr.push(line.product.id)
                }
            });
            if (arr.length === 0) {
                return true
            }
            // nếu tặng lẻ mà trùng sp thì k hiện khuyến mãi
            if (condition.apply_type === 'one') {
                // return arr.length !== 1;
                return false
            } else {
                // return arr.length < 1;
                return arr.length !== product_in_condition.length;
            }
        },
        CheckProductInPos: async function (order, condition) {
            let check = this.CheckApplyType(order, condition);
            if (check) {
                return
            }
            var self = this;
            let product_in_condition = [];
            condition.product_id.forEach((pr) => {
                product_in_condition.push(pr)
            });
            // Tặng gộp
            if (condition.apply_type === 'many') {
                order.orderlines.forEach((line) => {
                    if (_.indexOf(product_in_condition, line.product.id) !== -1) {
                        self.applyWithTypeBuyOtherGift(order, line, condition);
                    }
                })
            }
            // Tặng lẻ
            if (condition.apply_type === 'one') {
                let products_in_pos_valid = [];
                order.orderlines.forEach((line) => {
                    if (_.indexOf(product_in_condition, line.product.id) !== -1 && line.quantity >= condition.qty) {
                        products_in_pos_valid.push(line.product.id)
                    }
                });
                //lấy sản phẩm đầu tiên được thêm vào giỏ hàng trong cấu hình và phải đủ điều kiện
                let product_condition_add_first_pos
                product_in_condition.forEach((product) => {
                    if (products_in_pos_valid.indexOf(product) === 0) {
                        product_condition_add_first_pos = product
                    }
                })
                order.orderlines.forEach((line) => {
                    if (_.indexOf(product_in_condition, line.product.id) !== -1 && line.product.id === product_condition_add_first_pos) {
                        self.applyWithTypeBuyOtherGift(order, line, condition);
                    }
                })

            }

        },
        applyWithTypeBuyOtherGift: function (order, line, condition) {
            if (line.quantity < condition.qty) {
                return
            }
            if (line.quantity === condition.qty) {
                line.set_discount(100);
                line.setPromotion(condition.promotion_id[0])
                return;
            }
            if (line.quantity > condition.qty) {
                line.set_quantity(line.quantity - condition.qty);
                let product = this.db.get_product_by_id(line.product.id);
                let options = {
                    // price: 0,
                    price: line.price,
                    merge: false,
                    quantity: condition.qty,
                    discount: 100,
                    extras: {
                        promotion_id: this.id
                    }
                };
                order.add_product(product, options);
                // Them chi tiet combo neu co
                var combo_prod_detail = []
                combo_prod_detail.push(line.combo_prod_info)
                //Add lai combo detail
                order.orderlines.filter((orderline) => {
                    return orderline.product.id === product.id && product.x_is_combo
                }).forEach((line) => {
                    line.combo_prod_info = combo_prod_detail[0]
                })
            }
        },
        revertAppliedOnOrder: function (order) {
            Promotion.prototype.revertAppliedOnOrder.call(this, order);
            if (this.type !== 'gift_total_amount') {
                return;
            }
            let conditionOrderLine = this.getConditionOrderLineGiftTotalCondition(order)
            order.orderlines.filter(line => conditionOrderLine.includes(line.id)).forEach((line) => {
                // Fix when clear promotion;
                if (!line) return;
                line.promotion_applied_quantity = 0
            });
            let removeLines = order.orderlines.filter((line) => {
                if (!line.promotion_id) {
                    return;
                }
                let promotion_id = line.promotion_id;
                if (typeof promotion_id == 'object') {
                    promotion_id = promotion_id[0];
                }
                if (promotion_id != this.id) {
                    return;
                }
                return line;
            });
            removeLines.forEach((line) => {
                let product = line.product;
                let qty = line.quantity;
                order.remove_orderline(line);
                order.add_product(product, {
                    quantity: qty,
                });
                // Them chi tiet combo neu co
                var combo_prod_detail = []
                combo_prod_detail.push(line.combo_prod_info)
                //Add lai combo detail
                order.orderlines.filter((orderline) => {
                    return orderline.product.id === product.id && product.x_is_combo
                }).forEach((line) => {
                    line.combo_prod_info = combo_prod_detail[0]
                })
            });
        },
        getConditionOrderLineGiftTotalCondition: function (order) {
            let conditions = this.db.getPromotionGiftTotolAmountByPromotionIds([this.id])
            let conditionOrderLineId = []
            conditions.forEach((condition) => {
                if (condition.product_id) {
                    let conditionOrderLine = order.orderlines.filter(line => line.product.id === condition.product_id[0] && !line.promotion_id)
                    if (conditionOrderLine) {
                        conditionOrderLine.forEach((line) => {
                            conditionOrderLineId.push(line.id)
                        })
                    }
                } else if (condition.category_id) {
                    let conditionOrderLine = order.orderlines.filter(line => line.product.pos_categ_id[0] === condition.category_id[0] && !line.promotion_id)
                    if (conditionOrderLine) {
                        conditionOrderLine.forEach((line) => {
                            conditionOrderLineId.push(line.id)
                        })
                    }
                }
            })
            return conditionOrderLineId
        },
    });
    return models;

});