odoo.define('ev_pos_promotion_discount_condition.Promotion', function (require) {
    "use strict"

    const models = require('ev_pos_promotion.Promotion');
    const rpc = require('web.rpc');
    const Promotion = models.Promotion;
    models.Promotion = Promotion.extend({
        applyPromotionToOrder: function (order) {
            Promotion.prototype.applyPromotionToOrder.call(this, order);
            if (this.type !== 'discount_condition') {
                return;
            }
            if (!this.isValidOrder(order)) {
                return;
            }
            let self = this;
            let applies = this.db.getPromotionDiscountApplyByPromotionIds([this.id]);
            let arr_product_apply = []
            let arr_product_apply_in_pos = []
            applies.forEach((apply) => {
                arr_product_apply.push(apply.product_id[0])
            })
            order.orderlines.forEach((line) => {
                arr_product_apply_in_pos.push(line.product.id)
            })
            let id = []
            arr_product_apply.forEach((product_id) => {
                if (_.indexOf(arr_product_apply_in_pos, product_id) != -1) {
                    id.push(product_id)
                }
            })
            //áp dụng sản phẩm đauf tiên được thêm vào đơn hàng với tặng lẻ
            var arr_product_condition_inpos = [];
            order.orderlines.forEach((line) => {
                if (_.indexOf(arr_product_apply, line.product.id) !== -1) {
                    arr_product_condition_inpos.push(line.product.id)
                }
            });
            let product_condition_add_first_pos
            arr_product_apply.forEach((product) => {
                if (arr_product_condition_inpos.indexOf(product) === 0) {
                    product_condition_add_first_pos = product
                }
            })
            if (this.x_promotion_apply_or) {
                applies.forEach((apply) => {
                    // if (apply.product_id[0] === id[0]) {
                    if (apply.product_id[0] === product_condition_add_first_pos) {
                        self.applyForProduct(order, apply);
                    } else {
                        // self.applyForCategory(order, apply);
                    }
                });
            }
            if (!this.x_promotion_apply_or) {
                applies.forEach((apply) => {
                    if (apply.product_id) {
                        self.applyForProduct(order, apply);
                    } else {
                        // self.applyForCategory(order, apply);
                    }
                });
            }


            let conditions = this.db.getPromotionDiscountConditionByPromotionIds([this.id]);
            conditions.forEach((condition) => {
                if (condition.product_id) {
                    this.setAppliedQuantityProductDiscountCondition(order, condition)
                } else if (condition.category_id) {
                    this.setAppliedQuantityCategoryDiscountCondition(order, condition)
                }
            })
            order.save_to_db()
        },

        applyForProduct: function (order, apply) {
            let self = this;
            order.orderlines.forEach((line) => {
                if (apply.product_id[0] === line.product.id) {
                    if (line.product.id != apply.product_id[0] || line.promotion_id) {
                        return;
                    }
                    if (apply.apply_type == 'all') {
                        // self.applyWithTypeAll(line, apply);
                        self.applyWithTypeAll(order, line, apply);

                    } else {
                        self.applyWithTypeOne(order, line, apply);
                    }
                }
            });
        },

        applyForCategory: function (order, apply) {
            let self = this;
            order.orderlines.forEach((line) => {
                if (apply.category_id[0] === line.category_id) {
                    let product = self.db.get_product_by_id(line.product.id);
                    if (product.pos_categ_id[0] !== apply.category_id[0] ||
                        line.promotion_id) {
                        return;
                    }
                    if (apply.apply_type === 'all') {
                        // self.applyWithTypeAll(line, apply);
                        self.applyWithTypeAll(order, line, apply);
                    } else {
                        self.applyWithTypeOne(order, line, apply);
                    }
                }
            });
        },

        revertAppliedOnOrder: function (order) {
            Promotion.prototype.revertAppliedOnOrder.call(this, order);
            if (this.type !== 'discount_condition') {
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
                // order.remove_orderline(line);
                // order.add_product(product, {
                //     quantity: qty,
                // });
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

        applyWithTypeAll: function (order, line, apply) {
            if (apply.discount) {
                let product_km = this.db.get_product_by_id(this.product_id[0]);
                let amount = apply.discount / 100 * line.price * line.quantity;
                let options = {
                    price: amount * -1,
                    quantity: 1,
                    merge: false,
                    extras: {
                        promotion_id: this.id,
                        x_product_promotion: this.name,
                        x_sequence: this.id,
                        sequence_promotion: line.id
                    }
                }
                order.add_product(product_km, options);
                if (line.x_sequence === undefined) {
                    line.setx_sequence(this.id)
                }
                if (line.x_product_promotion === undefined) {
                    line.setProductPromotion(this.name)
                }
                if (line.x_product_promotion !== undefined) {
                    line.setProductPromotion(line.x_product_promotion + ', ' + this.name)
                }
                if (line.x_is_price_promotion !== undefined) {
                    line.setPricePromotion((amount).toFixed(0))
                }
                if (line.x_is_price_promotion === undefined) {
                    line.setPricePromotion((amount).toFixed(0))
                }
                if (line.sequence_promotion === undefined) {
                    line.set_sequence_promotion(line.id)
                }
            }
            if (apply.price_unit) {
                let product_km = this.db.get_product_by_id(this.product_id[0]);
                let options = {
                    price: apply.price_unit * -1 * line.quantity,
                    quantity: 1,
                    merge: false,
                    extras: {
                        promotion_id: this.id,
                        x_product_promotion: this.name,
                        x_sequence: this.id,
                        sequence_promotion: line.id
                    }
                }
                order.add_product(product_km, options);
                if (line.x_sequence === undefined) {
                    line.setx_sequence(this.id)
                }
                if (line.x_product_promotion === undefined) {
                    line.setProductPromotion(this.name)
                }
                if (line.x_product_promotion !== undefined) {
                    line.setProductPromotion(line.x_product_promotion + ', ' + this.name)
                }
                if (line.x_is_price_promotion !== undefined) {
                    line.setPricePromotion((apply.price_unit * line.quantity).toFixed(0))
                }
                if (line.x_is_price_promotion === undefined) {
                    line.setPricePromotion((apply.price_unit * line.quantity).toFixed(0))
                }
                if (line.sequence_promotion === undefined) {
                    line.set_sequence_promotion(line.id)
                }
            }
        },

        applyWithTypeOne: function (order, line, apply) {
            let product_km = this.db.get_product_by_id(this.product_id[0]);
            if (apply.discount) {
                let amount = apply.discount / 100 * line.price;
                let options = {
                    price: amount * -1,
                    quantity: 1,
                    merge: false,
                    extras: {
                        promotion_id: this.id,
                        x_product_promotion: this.name,
                        x_sequence: this.id,
                        sequence_promotion: line.id
                    }
                };
                order.add_product(product_km, options);
                if (line.x_sequence === undefined) {
                    line.setx_sequence(this.id)
                }
                if (line.x_product_promotion === undefined) {
                    line.setProductPromotion(this.name)
                }
                if (line.x_product_promotion !== undefined) {
                    line.setProductPromotion(line.x_product_promotion + ', ' + this.name)
                }
                if (line.x_is_price_promotion !== undefined) {
                    line.setPricePromotion((amount).toFixed(0))
                }
                if (line.x_is_price_promotion === undefined) {
                    line.setPricePromotion((amount).toFixed(0))
                }
                if (line.sequence_promotion === undefined) {
                    line.set_sequence_promotion(line.id)
                } else {
                    // line.setPricePromotion((line.x_is_price_promotion + amount).toFixed(0))
                }
            }
            if (apply.price_unit) {
                let options = {
                    price: apply.price_unit * -1,
                    quantity: 1,
                    merge: false,
                    extras: {
                        promotion_id: this.id,
                        x_product_promotion: this.name,
                        type: this.type,
                        x_sequence: this.id,
                        sequence_promotion: line.id
                    }
                };
                order.add_product(product_km, options);
                if (line.x_sequence === undefined) {
                    line.setx_sequence(this.id)
                }
                if (line.x_product_promotion === undefined) {
                    line.setProductPromotion(this.name)
                }
                if (line.x_product_promotion !== undefined) {
                    line.setProductPromotion(line.x_product_promotion + ', ' + this.name)
                }
                if (line.x_is_price_promotion !== undefined) {
                    line.setPricePromotion((apply.price_unit).toFixed(0))
                }
                if (line.x_is_price_promotion === undefined) {
                    line.setPricePromotion((apply.price_unit).toFixed(0))
                }
                if (line.sequence_promotion === undefined) {
                    line.set_sequence_promotion(line.id)
                }

            }
        },

        setAppliedQuantityProductDiscountCondition: function (order, condition) {
            let conditionOrderLine = order.orderlines.filter(line => line.product.id === condition.product_id[0] && !line.promotion_id)
            this.setAppliedQuantityDiscountCondition(conditionOrderLine, condition)
        },

        setAppliedQuantityCategoryDiscountCondition: function (order, condition) {
            let conditionOrderLine = order.orderlines.filter(line => line.product.pos_categ_id[0] === condition.category_id[0] && !line.promotion_id)
            this.setAppliedQuantityDiscountCondition(conditionOrderLine, condition)
        },

        setAppliedQuantityDiscountCondition: function (conditionOrderLine, condition) {
            let conditionQty = condition.qty
            conditionOrderLine.forEach((line) => {
                if (conditionQty <= 0) {
                    return;
                }
                let oldAppliedQty = line.getAppliedPromotionQuantity()
                line.promotion_applied_quantity = oldAppliedQty
                if (line.quantity - oldAppliedQty >= conditionQty) {
                    line.promotion_applied_quantity += conditionQty
                    conditionQty = 0
                } else {
                    line.promotion_applied_quantity = line.quantity
                    conditionQty -= line.quantity - oldAppliedQty
                }
            })
        },

        isValidOrder: function (order, show) {
            let res = Promotion.prototype.isValidOrder.call(this, order, show);
            if (this.type !== 'discount_condition') {
                return res;
            }
            // if (!this.check_promotion){
            //     return res
            // }
            // thêm hiện chương trình khuyến mại
            var test_pro;
            const check_pro = async () => {
                return await this.check(this.id, this.id)
            };
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
            // let [conditionAmount, conditionProductIds, conditionCategoryIds, applyProductIds, applyCategoryIds] = this.getPromotionRequirementsOrder();
            let [conditionProductIds, conditionCategoryIds, applyProductIds, applyCategoryIds] = this.getPromotionRequirementsOrder();

            let isValidOrderAmount = this.isValidOrderAmount(order, this.total_amount);
            let isValidCategory = this.isValidCategory(order, conditionCategoryIds, show);
            let isValidProduct = this.isValidProduct(order, conditionProductIds, show);
            let isValidCategoryApply = this.isValidCategoryApply(order, applyCategoryIds);
            let isValidProductApply = this.isValidProductApply(order, applyProductIds);
            // console.log('isValidProductApply', isValidProductApply)
            if (!isValidOrderAmount) {
                return false;
            }
            let isValidProductAndCategory = conditionProductIds.length > 0 && isValidProduct && conditionCategoryIds.length > 0 && isValidCategory;
            let isValidProductNotCategory = conditionProductIds.length > 0 && conditionCategoryIds.length <= 0 && isValidProduct;
            let isValidCategoryNotProduct = conditionCategoryIds.length > 0 && conditionProductIds.length <= 0 && isValidCategory;

            return (isValidProductAndCategory || isValidProductNotCategory || isValidCategoryNotProduct) && (isValidCategoryApply || isValidProductApply)
        },

        isValidOrderAmount: function (order, amount) {
            return !(order.get_total_with_tax() < amount && amount != 0);
        },

        isValidProduct: function (order, conditionProductIds, show) {
            let self = this;
            let orderProductIds = [];
            let orderProductQty = {};
            order.orderlines.forEach((line) => {
                // Không tính các line đã được tính cho promotion khác
                let promotionId = this.parsePromotionId(line.promotion_id);
                if (promotionId && promotionId != self.id) {
                    return;
                }
                let appliedPromotionQty = line.getAppliedPromotionQuantity(show);
                // Chỉ kiểm tra các sản phẩm có trong list promotion condition
                if (_.indexOf(conditionProductIds, line.product.id) != -1) {
                    orderProductIds.push(line.product.id);
                    if (!orderProductQty.hasOwnProperty(line.product.id)) {
                        orderProductQty[line.product.id] = line.quantity - appliedPromotionQty
                    } else {
                        orderProductQty[line.product.id] += line.quantity - appliedPromotionQty
                    }

                }
            });
            if (this.x_promotion_condition_or) {
                // sửa điều kiện hoặc trong điều kiện áp dụng CTKM (mua A or B or C) thì được áp dụng
                if (orderProductIds.length === 0) {
                    return false
                }
            }
            if (!this.x_promotion_condition_or) {
                let _diff = _.difference(conditionProductIds, orderProductIds);
                if (_diff.length > 0) {
                    return false;
                }
            }

            return this.isValidProductQuantity(orderProductQty);
        },

        isValidProductQuantity: function (orderProductQty) {
            let conditions =
                this.db.getPromotionDiscountConditionByPromotionIds([this.id]);

            let notValidConditions = conditions.filter((item) => {
                return item.qty > orderProductQty[item.product_id[0]];
            });

            if (this.x_promotion_condition_or){
                if (Object.keys(orderProductQty).length > notValidConditions.length){
                    return true;
                }
            }

            if (notValidConditions.length > 0) {
                return false;
            }
            return true;
        },

        isValidProductApply: function (order, applyProductIds) {
            let self = this;
            let orderApplyProductIds = [];
            order.orderlines.forEach((line) => {
                // Không tính các line đã được tính cho promotion khác
                let promotionId = this.parsePromotionId(line.promotion_id);
                if (promotionId && promotionId != self.id) {
                    return;
                }
                // kiểm tra sản phẩm được áp dụng trong đơn
                if (_.indexOf(applyProductIds, line.product.id) != -1) {
                    orderApplyProductIds.push(line.product.id);
                }
            })
            if (this.x_promotion_apply_or) {
                return orderApplyProductIds.length
            }
            if (!this.x_promotion_apply_or) {
                //điều kiện và
                // if (applyProductIds.length === orderApplyProductIds.length) {
                //     return orderApplyProductIds.length
                // }
                // return 0
                return orderApplyProductIds.length

            }
            return orderApplyProductIds.length

        },

        isValidCategory: function (order, conditionCategoryIds, show) {
            let self = this;
            let orderCategoryIds = [];
            let orderCategoryQty = {};
            order.orderlines.forEach((line) => {
                // Không tính các line đã được tính cho promotion khác
                let promotionId = this.parsePromotionId(line.promotion_id);
                if (promotionId && promotionId != self.id) {
                    return;
                }

                let product = self.db.get_product_by_id(line.product.id);
                let pos_categ_id = product.pos_categ_id[0];
                let appliedPromotionQty = line.getAppliedPromotionQuantity(show)
                // kiểm tra số lượng nhóm sản phẩm theo điều kiện
                if (_.indexOf(conditionCategoryIds, pos_categ_id) != -1) {
                    orderCategoryIds.push(pos_categ_id);
                    if (!orderCategoryQty.hasOwnProperty(pos_categ_id)) {
                        orderCategoryQty[pos_categ_id] = line.quantity - appliedPromotionQty
                    } else {
                        orderCategoryQty[pos_categ_id] += line.quantity - appliedPromotionQty
                    }
                }
            });
            orderCategoryIds = _.uniq(orderCategoryIds);

            let _diff = _.difference(conditionCategoryIds, orderCategoryIds);
            if (_diff.length > 0) {
                return false;
            }

            return this.isValidCategoryQuantity(orderCategoryQty);

        },

        isValidCategoryQuantity: function (orderCategoryQty) {
            let conditions =
                this.db.getPromotionDiscountConditionByPromotionIds([this.id]);
            let totalConditionCategoryQty = this.getConditionCategoryQty(conditions)
            let notValidConditions = conditions.filter((item) => {
                return orderCategoryQty[item.category_id[0]] < totalConditionCategoryQty[item.category_id[0]]
            });
            return notValidConditions.length <= 0;
        },

        isValidCategoryApply: function (order, applyCategoryIds) {
            let self = this;
            let orderApplyCategoryIds = [];
            order.orderlines.forEach((line) => {
                // Không tính các line đã được tính cho promotion khác
                let promotionId = this.parsePromotionId(line.promotion_id);
                if (promotionId && promotionId != self.id) {
                    return;
                }

                let product = self.db.get_product_by_id(line.product.id);
                let pos_categ_id = product.pos_categ_id[0];
                // kiểm tra nhóm sản phẩm có trong CTKM
                if (_.indexOf(applyCategoryIds, pos_categ_id) != -1) {
                    orderApplyCategoryIds.push(pos_categ_id)
                }
            });
            return orderApplyCategoryIds.length
        },

        parsePromotionId: function (promotion) {
            if (Array.isArray(promotion)) {
                return promotion[0];
            } else if (typeof promotion === 'object') {
                return promotion.id;
            }
            return promotion
        },

        getPromotionRequirementsOrder: function () {
            let conditions =
                this.db.getPromotionDiscountConditionByPromotionIds([this.id]);
            let applies = this.db.getPromotionDiscountApplyByPromotionIds([this.id]);

            let conditionProductIds = [];
            let conditionCategoryIds = [];
            let applyProductIds = [];
            let applyCategoryIds = [];
            // let amount = 0;

            conditions.forEach((item) => {
                // amount = amount > item.total_amount ? amount : item.total_amount;
                if (item.product_id)
                    conditionProductIds.push(item.product_id[0]);
                if (item.category_id)
                    conditionCategoryIds.push(item.category_id[0]);
            });

            applies.forEach((item) => {
                if (item.product_id)
                    applyProductIds.push(item.product_id[0]);
                if (item.category_id)
                    applyCategoryIds.push(item.category_id[0]);
            });

            // return [amount, conditionProductIds, conditionCategoryIds, applyProductIds, applyCategoryIds];
            return [conditionProductIds, conditionCategoryIds, applyProductIds, applyCategoryIds];
        },

        initFromJson: function (json) {
            Promotion.prototype.initFromJson(json);
            this.promotion_discount_condition_ids = json.promotion_discount_condition_ids;
            this.promotion_discount_apply_ids = json.promotion_discount_apply_ids;
        },

        exportToJson: function () {
            let json = Promotion.prototype.exportToJson();
            json.promotion_discount_condition_ids = this.promotion_discount_condition_ids;
            json.promotion_discount_apply_ids = this.promotion_discount_apply_ids;
            return json;
        },

        getConditionOrderLineDiscountCondition: function (order) {
            let conditions = this.db.getPromotionDiscountConditionByPromotionIds([this.id])
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
