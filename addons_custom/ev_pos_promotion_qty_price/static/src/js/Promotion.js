odoo.define('ev_pos_promotion_qty_price.Promotion', function (require) {
    "use strict"

    const models = require('ev_pos_promotion.Promotion');
    const rpc = require('web.rpc');
    const Promotion = models.Promotion;
    models.Promotion = Promotion.extend({
        initFromJson: function (json) {
            Promotion.prototype.initFromJson(json);
            this.pos_promotion_qty_price_ids = json.pos_promotion_qty_price_ids;
        },

        exportToJson: function () {
            let json = Promotion.prototype.exportToJson();
            json.pos_promotion_qty_price_ids = this.pos_promotion_qty_price_ids;
            return json;
        },

        isValidOrder: function (order, show) {
            let res = Promotion.prototype.isValidOrder.call(this, order, show);
            if (this.type != 'qty_price') {
                return res
            }
            // if (!this.check_promotion){
            //     return res
            // }

            // check in time
            let isValidTime = this.isValidTime()
            if (!isValidTime) {
                return res;
            }
            // check partner for not apply promotion
            let isValidPartnerNot = this.isValidPartnerNot(order);
            if (!isValidPartnerNot) {
                return res
            }
            // check partner for apply promotion
            let isValidPartner = this.isValidPartner(order)
            if (!isValidPartner) {
                return res;
            }
            // Kiểm tra giá trị đơn hàng có lớn hơn giá trị điều kiện không,
            // Nếu không có giá trị thì thông tính
            if (order.get_total_with_tax() < this.total_amount && this.total_amount !== 0) {
                return false;
            }
            // logic check if order is valid for apply promotion
            let OrderLineProducts = this.getOrderLineProductsQty(order, show);
            let OrderLineProductCategories = this.getOrderLineCategoriesQty(order, show);
            let promotionsQtyPrice = this.db.getPromotionQuantityPriceByPromotionIds([this.id])
            let isvalidOrder = false;
            promotionsQtyPrice.forEach((promotion) => {
                if (promotion.product_id) {
                    if (promotion.qty === 0) {
                        if (OrderLineProducts[promotion.product_id[0]]) {
                            isvalidOrder = true
                        }
                    } else if (OrderLineProducts[promotion.product_id[0]] && OrderLineProducts[promotion.product_id[0]] >= promotion.qty) {
                        //chỉ check có sản phẩm trong giỏ hàng không
                        // if (OrderLineProducts[promotion.product_id[0]]) {
                        isvalidOrder = true;
                    }

                } else if (promotion.category_id) {
                    if (OrderLineProductCategories[promotion.category_id[0]] && OrderLineProductCategories[promotion.category_id[0]] >= promotion.qty) {
                        isvalidOrder = true
                    }
                }
            })
            return isvalidOrder
        },

        filterValidRulePromotionQuantityPrice: function (order, rules) {
            let OrderLineProducts = this.getOrderLineProductsQty(order);
            let OrderLineProductCategories = this.getOrderLineCategoriesQty(order);
            let Rules = [];
            rules.forEach((item) => {
                if (item.product_id) {
                    if (OrderLineProducts[item.product_id[0]] && OrderLineProducts[item.product_id[0]] >= item.qty) {
                    // check chỉ cần có SP trong đơn hàng thì áp dụng CTKM
                    // if (OrderLineProducts[item.product_id[0]]) {
                        Rules.push(item)
                    }
                } else if (item.category_id) {
                    if (OrderLineProductCategories[item.category_id[0]] && OrderLineProductCategories[item.category_id[0]] >= item.qty) {
                        Rules.push(item)
                    }
                }
            });
            if (Rules.length < 1) {
                return false;
            }
            return Rules.sort(function (first, second) {
                let left = first.product_id ? 1 : 0;
                let right = second.product_id ? 1 : 0;
                return right - left || second.qty - first.qty;
            });
        },

        applyPromotionToOrder: function (order) {
            Promotion.prototype.applyPromotionToOrder.call(this, order);
            if (this.type != 'qty_price') {
                return;
            }
            if (!this.isValidOrder(order)) {
                return;
            }
            let rules = this.db.getPromotionQuantityPriceByPromotionIds([this.id]);
            let rule = this.filterValidRulePromotionQuantityPrice(order, rules);
            if (!rule) {
                return;
            }
            let product_in_rule = []
            rule.forEach((rl) => {
                if (_.indexOf(product_in_rule, rl.product_id[0]) === -1) {
                    product_in_rule.push(rl.product_id[0])
                }
            })
            var rule_test = []
            rule.reverse().forEach((rl) => {
                product_in_rule.forEach((product) => {
                    if (rl.product_id[0] === product) {
                        rule_test.forEach((pr) => {
                            if (pr.product_id[0] === product) {
                                rule_test = rule_test.filter(item => item !== pr);
                            }
                        })
                        rule_test.push(rl)
                    }
                });
            });
            rule_test.forEach((rule_line) => {
                if (rule_line.product_id) {
                    // áp dụng với sản phẩm
                    this.applyForProductQtyPrice(order, rule_line);
                } else if (rule_line.category_id) {
                    // áp dụng với nhóm sản phẩm
                    this.applyForCategoryQtyPrice(order, rule_line);
                }
            })
            order.save_to_db()
        },

        applyForProductQtyPrice: function (order, rule_line) {
            let apply_orderlines = ([order.orderlines.filter((line) => {
                let quantity = line.quantity - line.getAppliedPromotionQuantity()
                // nếu check trong sp có trong orderline thì áp dụng CTKM
                return line.product.id === rule_line.product_id[0] && !line.promotion_id
            }), rule_line.price_unit])
            apply_orderlines[0].forEach((line) => {
                // nếu check trong sp có trong orderline thì áp dụng CTKM
                if (rule_line.check_discount_price === 'price') {
                    let product_km = this.db.get_product_by_id(this.product_id[0]);
                    let options = {
                        price: rule_line.price_unit * -1 * line.quantity,
                        quantity: 1,
                        merge: false,
                        extras: {
                            promotion_id: this.id,
                            x_product_promotion: this.name,
                            x_sequence: this.id,
                            sequence_promotion: line.id
                        }
                    }

                    // line.set_sequence_promotion(line.id)
                    order.add_product(product_km, options);
                    if (line.x_product_promotion === undefined) {
                        line.setProductPromotion(this.name)
                    }
                    if (line.x_product_promotion !== undefined) {
                        line.setProductPromotion(line.x_product_promotion + ', ' + this.name)
                    }
                    if (line.x_sequence === undefined) {
                        line.setx_sequence(this.id);
                    }
                    if (line.x_is_price_promotion !== undefined) {
                        line.setPricePromotion((rule_line.price_unit * line.quantity).toFixed(0))
                    }
                    if (line.x_is_price_promotion === undefined) {
                        line.setPricePromotion((rule_line.price_unit * line.quantity).toFixed(0))
                    }
                    if (line.sequence_promotion === undefined) {
                        line.set_sequence_promotion(line.id)
                    }
                }
                // nếu check trong sp có trong orderline thì áp dụng CTKM
                if (rule_line.check_discount_price === 'discount') {
                    let product_km = this.db.get_product_by_id(this.product_id[0]);
                    let amount = rule_line.discount / 100 * line.price * line.quantity;
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
                    if (line.x_product_promotion === undefined) {
                        line.setProductPromotion(this.name)
                    }
                    if (line.x_product_promotion !== undefined) {
                        line.setProductPromotion(line.x_product_promotion + ', ' + this.name)
                    }
                    if (line.x_sequence === undefined) {
                        line.setx_sequence(this.id);
                    }
                    if (line.x_is_price_promotion !== undefined) {
                        line.setPricePromotion(amount.toFixed(0))
                    }
                    if (line.x_is_price_promotion === undefined) {
                        line.setPricePromotion(amount.toFixed(0))
                    }
                    if (line.sequence_promotion === undefined) {
                        line.set_sequence_promotion(line.id)
                    }
                }

            })
        },

        applyForCategoryQtyPrice: function (order, rule_line) {
            let categoryQty = 0
            var apply_orderlines = order.orderlines.filter((line) => {
                if (line.product.pos_categ_id[0] === rule_line.category_id[0] && !line.promotion_id) {
                    categoryQty += line.quantity
                    return true
                }
                return false
            }).sort(function (first, second) {
                return second.price - first.price;
            });
            let maxQtyApply = categoryQty - categoryQty % rule_line.qty
            if (maxQtyApply !== 0) {
                apply_orderlines.forEach((line) => {
                    let quantity = line.quantity - line.getAppliedPromotionQuantity()
                    if (maxQtyApply === 0) {
                        return;
                    }
                    if (maxQtyApply >= quantity) {
                        maxQtyApply = maxQtyApply - quantity
                    } else {
                        let oldQuantity = quantity
                        line.set_quantity(maxQtyApply)
                        let options = {
                            quantity: oldQuantity - maxQtyApply,
                            merge: false,
                        }
                        order.add_product(line.product, options);
                    }
                    line.set_unit_price(rule_line.price_unit)
                    line.setPromotion(rule_line.promotion_id[0])
                    line.promotion_applied_quantity = line.quantity
                })
            }
        },

        revertAppliedOnOrder: function (order) {
            Promotion.prototype.revertAppliedOnOrder.call(this, order);
            // Lọc lại dữ liệu promotion để chi lấy type === 'qty_price'
            if (this.type != 'qty_price' || !order.orderlines) {
                return;
            }
            //Clear all applied order of promotion
            let pricelist = order.pricelist
            order.orderlines.filter((orderline) => {
                return orderline.getPromotionId() === this.id
            }).forEach((line) => {
                // Fix when clear promotion;
                if (!line) return;
                let product = line.product;
                order.remove_orderline(line);
                line.promotion_id = undefined
                line.promotion_applied_quantity = 0
            });
        },

    });

    return models;

})
