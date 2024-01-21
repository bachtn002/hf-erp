odoo.define('ev_pos_promotion_total_price_buy_other_product.Promotion', function (require) {
    "use strict"
    const models = require('ev_pos_promotion.Promotion');
    const Promotion = models.Promotion;
    const rpc = require('web.rpc');
    models.Promotion = Promotion.extend({

        isValidOrder: function (order, show) {
            let args = [this.id, this.id];
            let res = Promotion.prototype.isValidOrder.call(this, order, show);
            if (this.type !== 'total_price_buy_other_product') {
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
            let isValidPartner = this.isValidPartner(order);
            if (!isValidPartner) {
                return res
            }
            let [conditionAmount, applyProductIds] = this.getPromotionRequirementsOrderBuyOther();

            //kiểm tra số lượng sp
            let conditions =
                this.db.getPromotionTotalPriceBuyOtherProductByPromotionIds([this.id]);
            let arr = []
            conditions.forEach((condition) => {
                arr.push(condition.total_price)
                // this.CheckProductInPos(order, condition)
            });
            // lưu giá trị điều kiện lớn nhất CTKM phù hợp với đơn hàng
            let arr_price_condition = []; //mảng lưu giá trị đơn hàng điều kiện lớn nhất được áp dụng

            arr.forEach((ar) => {
                if (order.get_total_with_tax() >= ar) {
                    arr_price_condition = [];
                    arr_price_condition.push(ar)
                }
            });
            let checkQtyProduct;
            let arr_checkQtyProduct = [];//kiểm tra nế sp gộp thì k hiện chương trình khuyến mại
            conditions.forEach((condition) => {
                if (condition.total_price === arr_price_condition[0]) {
                    checkQtyProduct = this.checkQtyProduct(order, condition);
                    arr_checkQtyProduct.push(checkQtyProduct)
                }
            });
            let flag_check;
            if (_.indexOf(arr_checkQtyProduct, 1) !== -1) {
                flag_check = true
            }
            // kiểm tra giá trị đơn hàng so với điều kiện CTKM
            let isValidOrderAmountBuyOther = this.isValidOrderAmountBuyOther(order, conditionAmount);

            let applyProductIdsCurrentAmount = this.isValidProductApplyBuyOtherWithCurrentAmount(order, applyProductIds);
            let isValidProductApplyBuyOther = this.isValidProductApplyBuyOther(order, applyProductIdsCurrentAmount);
            return (isValidProductApplyBuyOther);
        },
        isValidProductApplyBuyOtherWithCurrentAmount(order, applyProductIds) {
            let applyProductIdsCurrentAmount = [];
            let total_in_pos = order.get_total_with_tax();
            let conditions =
                this.db.getPromotionTotalPriceBuyOtherProductByPromotionIds([this.id]);
            conditions.forEach((item) => {
                if (item.total_price <= total_in_pos) {
                    applyProductIdsCurrentAmount.push(item.product_id[0])
                }
            })
            return applyProductIdsCurrentAmount
        },
        isValidProductApplyBuyOther: function (order, applyProductIdsCurrentAmount) {  //kiểm tra sản phẩm trên pos có trong điều kiện k
            let orderApplyProductIds = [];
            let conditions =
                this.db.getPromotionTotalPriceBuyOtherProductByPromotionIds([this.id]);
            var map_promotion_condition = new Map()
            conditions.forEach((condition) => {
                map_promotion_condition.set(condition.product_id[0], condition.qty)
            });
            order.orderlines.forEach((line) => {
                applyProductIdsCurrentAmount.forEach((item) => {
                    if (item === line.product.id) {
                        orderApplyProductIds.push(line.product.id)
                    }
                })
            })
            return orderApplyProductIds.length

        },
        isValidOrderAmountBuyOther: function (order, amounts) {

            //xác định giá nhỏ nhất trong điều kiện CTKM
            var lowest = Number.POSITIVE_INFINITY;
            var tmp;
            amounts.forEach((amount) => {
                tmp = amount
                if (tmp < lowest) lowest = tmp;
            });
            // kiểm tra nếu giá trị đơn hàng nhỏ hơn thì trả false
            if (order.get_total_with_tax() < lowest && lowest !== 0) {
                return false;
            }
            return true
        },
        applyPromotionToOrder: function (order) {
            Promotion.prototype.applyPromotionToOrder.call(this, order);
            if (this.type !== 'total_price_buy_other_product') {
                return;
            }
            if (!this.isValidOrder(order)) {
                return;
            }
            let self = this;
            let rules = this.db.getPromotionTotalPriceBuyOtherProductByPromotionIds([this.id]);
            let arr = []
            var total_before = order.get_total_with_tax();
            rules.forEach((rule) => {
                if (total_before >= rule.total_price) {
                    arr.push(rule.total_price);
                }
            });
            // lấy các rule có số lượng lớn nhất
            let arr_max_in_order = []
            rules.forEach((rule) => {
                if (total_before >= rule.total_price) {
                    arr_max_in_order.push(rule)
                }
            })
            let test = [];
            arr.forEach((ar) => {
                if (order.get_total_with_tax() >= ar) {
                    // test = [];
                    test.push(ar)
                }
            });
            var sequence = 0;
            arr_max_in_order.forEach((rule) => {
                this.applyForProductBuyOther(order, rule);
            })

        },
        applyForProductBuyOther: function (order, rule) {
            let self = this;
            order.orderlines.forEach((line) => {
                if(line.product.id == rule.product_id[0]){
                    self.applyWithTypeBuyOther(order, line, rule);
                }
            });
        },
        applyWithTypeBuyOther: function (order, line, rule) {
            if (rule.price_unit) {
                let product = this.db.get_product_by_id(rule.product_id[0]);
                let price_before = line.price - rule.price_unit;
                let product_km = this.db.get_product_by_id(this.product_id[0]);
                var amount_promotion = 0;
                if(rule.qty > line.quantity){
                    amount_promotion = rule.price_unit * -1 * line.quantity;
                } else {
                    amount_promotion = rule.price_unit * -1 * rule.qty;
                }
                if (amount_promotion == 0){
                    return;
                }
                let options = {
                    price: amount_promotion,
                    quantity: 1,
                    merge: false,
                    extras: {
                        promotion_id: this.id,
                        x_product_promotion: this.name,
                        x_sequence: this.id + line.id,
                        sequence_promotion: line.id
                    }
                }
                order.add_product(product_km, options);
                line.setProductPromotion(this.name);
                line.setx_sequence(this.id + line.id);
                if (line.x_is_price_promotion !== undefined) {
                    line.setPricePromotion(parseFloat((Math.abs(amount_promotion)).toFixed(0)))
                }
                if (line.x_is_price_promotion === undefined) {
                    line.setPricePromotion(parseFloat((Math.abs(amount_promotion)).toFixed(0)))
                }
                if (line.sequence_promotion === undefined) {
                    line.set_sequence_promotion(line.id)
                }
            } else {
                let product_km = this.db.get_product_by_id(this.product_id[0]);
                var amount = rule.discount / 100 * line.price;
                var amount_promotion = 0;
                if(rule.qty > line.quantity){
                    amount_promotion = amount * -1 * line.quantity;
                } else {
                    amount_promotion = amount * -1 * rule.qty;
                }
                if (amount_promotion == 0){
                    return;
                }
                let options = {
                    price: amount_promotion,
                    quantity: 1,
                    merge: false,
                    extras: {
                        promotion_id: this.id,
                        x_product_promotion: this.name,
                        x_sequence: this.id + line.id,
                        sequence_promotion: line.id
                    }
                }
                order.add_product(product_km, options);
                line.setProductPromotion(this.name);
                line.setx_sequence(this.id + line.id);
                if (line.x_is_price_promotion !== undefined) {
                    line.setPricePromotion(parseFloat((Math.abs(amount_promotion)).toFixed(0)))
                }
                if (line.x_is_price_promotion === undefined) {
                    line.setPricePromotion(parseFloat((Math.abs(amount_promotion)).toFixed(0)))
                }
                if (line.sequence_promotion === undefined) {
                    line.set_sequence_promotion(line.id)
                }
            }
            console.log('This', this);
            console.log('order', order);
        },
        checkQtyProduct: function (order, condition) {
            let product_in_condition = [];
            let product_in_pos = [];
            condition.product_id.forEach((pr) => {
                product_in_condition.push(pr)
            });
            order.orderlines.forEach((line) => {
                product_in_pos.push(line.product.id)
            });
            let arr = [];
            order.orderlines.forEach((line) => {
                if (_.indexOf(product_in_condition, line.product.id) !== -1) {
                    arr.push(line.product.id)
                }
            });
            return arr.length

        },
        getPromotionRequirementsOrderBuyOther: function () {
            let conditions =
                this.db.getPromotionTotalPriceBuyOtherProductByPromotionIds([this.id]);
            let applyProductIds = [];
            let total = [];
            conditions.forEach((item) => {
                if (item.product_id)
                    applyProductIds.push(item.product_id[0]);
            });
            conditions.forEach((item) => {
                if (_.indexOf(total, item.total_price) === -1) {
                    total.push(item.total_price)
                }
            });
            return [total, applyProductIds];
        },
        revertAppliedOnOrder: function (order) {
            Promotion.prototype.revertAppliedOnOrder.call(this, order);
            if (this.type !== 'total_price_buy_other_product') {
                return;
            }
            // revert promotion applied quantity in condition order line
            let conditionOrderLine = this.getConditionOrderLineDiscountCondition(order)
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
                let price = line.price;
                if (price < 0) {
                    order.remove_orderline(line);
                }
                if (price >= 0) {
                    order.remove_orderline(line);
                    order.add_product(product, {
                        quantity: qty,
                    });
                }
            });
        },
        initFromJson: function (json) {
            Promotion.prototype.initFromJson(json);
            this.pos_promotion_total_price_buy_other_product_ids = json.pos_promotion_total_price_buy_other_product_ids;
        },
        exportToJson: function () {
            let json = Promotion.prototype.exportToJson();
            json.pos_promotion_total_price_buy_other_product_ids = this.pos_promotion_total_price_buy_other_product_ids;
            return json;
        }
    });
    return models;
});