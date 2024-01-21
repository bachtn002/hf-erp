odoo.define('ev_pos_promotion_gift_condition.Promotion', function (require) {
    "use strict"

    const models = require('ev_pos_promotion.Promotion');
    const rpc = require('web.rpc');
    const Promotion = models.Promotion;
    models.Promotion = Promotion.extend({
        initFromJson: function (json) {
            Promotion.prototype.initFromJson(json);
            this.pos_promotion_gift_condition_ids = json.pos_promotion_gift_condition_ids;
            this.pos_promotion_gift_apply_ids = json.pos_promotion_gift_apply_ids;
        },

        exportToJson: function () {
            let json = Promotion.prototype.exportToJson();
            json.pos_promotion_gift_condition_ids = this.pos_promotion_gift_condition_ids;
            json.pos_promotion_gift_apply_ids = this.pos_promotion_gift_apply_ids;
            return json;
        },

        isValidOrder: function (order, show) {
            let res = Promotion.prototype.isValidOrder.call(this, order, show);
            if (this.type !== 'gift_condition') {
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
            let conditions = this.db.getPromotionGiftConditionByPromotionIds([this.id]);
            let conditions_apply = this.db.getPromotionGiftApplyByPromotionIds([this.id]);
            if (conditions.length < 1) {
                return false;
            }
            let amount = this.total_amount;
            // conditions.forEach((item) => {
            //     amount = amount > item.total_amount ? amount : item.total_amount
            // });
            // Kiêm tra giá trị đơn hàng có lớn hơn giá trị điều kiện không,
            // Nếu không có giá trị thì thông tính
            if (order.get_total_with_tax() < amount && amount !== 0) {
                return false;
            }
            // lấy số lượng thực tế sản phẩm và nhóm sản phẩm có thể áp dụng trên đơn
            let orderProductQty = this.getOrderLineProductsQty(order, show)
            let orderCategoryQty = this.getOrderLineCategoriesQty(order, show)
            // kiểm tra số lượng

            // thêm điều kiện hoặc trong sản phẩm áp dụng
            // let validOrder = false
            let totalConditionCategoryQty = this.getConditionCategoryQty(conditions)
            let validOrder_condition = false
            let shouldSkip = false;
            conditions.forEach((condition) => {
                if (shouldSkip) {
                    return;
                }
                let isValidProduct = condition.product_id && orderProductQty[condition.product_id[0]] >= condition.qty
                let isValidCategory = condition.category_id && orderCategoryQty[condition.category_id[0]] >= totalConditionCategoryQty[condition.category_id[0]]
                // if (!(isValidProduct || isValidCategory)) {
                //     validOrder = false
                // }
                if (this.x_promotion_condition_or) {
                    // thêm điều kiện hoặc trong sản phẩm áp dụng
                    if ((isValidProduct || isValidCategory)) {
                        validOrder_condition = true
                    }
                    // if ((!isValidProduct && !isValidCategory)) {
                    //     validOrder_condition = false
                    // }
                }
                if (!this.x_promotion_condition_or) {
                    if (!(isValidProduct || isValidCategory)) {
                        validOrder_condition = false
                        shouldSkip = true;
                        return;
                    }
                    if (isValidProduct || isValidCategory) {
                        validOrder_condition = true
                    }
                }
            })
            let validOrder = true
            let check_isValidProduct = []
            conditions_apply.forEach((condition) => {
                let isValidProduct = condition.product_id && orderProductQty[condition.product_id[0]] >= condition.qty
                let isValidCategory = condition.category_id && orderCategoryQty[condition.category_id[0]] >= totalConditionCategoryQty[condition.category_id[0]]
                // thêm điều kiện hoặc
                if (!isValidProduct) {
                    check_isValidProduct.push(condition.product_id)
                }
                if (this.x_promotion_apply_or) {
                    // thêm điều kiện hoặc trong sản phẩm áp dụng
                    if ((isValidProduct || isValidCategory)) {
                        validOrder = true
                    }
                }
                if (!this.x_promotion_apply_or) {
                    if (!(isValidProduct || isValidCategory)) {
                        validOrder = false
                    }
                    // if (isValidProduct || isValidCategory) {
                    //     validOrder = true
                    // }
                }
            });
            if (check_isValidProduct.length === conditions_apply.length) {
                validOrder = false
            }
            let result;
            if (!validOrder_condition) {
                result = false
            }
            if (validOrder_condition && !validOrder) {
                result = false
            }
            if (validOrder_condition && validOrder) {
                result = true;
            }
            return result
        },

        applyPromotionToOrder: function (order) {
            Promotion.prototype.applyPromotionToOrder.call(this, order);
            if (this.type !== 'gift_condition') {
                return;
            }
            if (!this.isValidOrder(order)) {
                return;
            }
            let applies = this.db.getPromotionGiftApplyByPromotionIds([this.id]);
            let conditions = this.db.getPromotionGiftConditionByPromotionIds([this.id])
            if (this.x_promotion_apply_or) {
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
                    if (_.indexOf(arr_product_apply_in_pos, product_id) !== -1) {
                        id.push(product_id)
                    }
                })
                //áp dụng CTKM với sp được thêm đầu tiên trong giỏ hàng
                let arr_before_product = []
                order.orderlines.forEach((line) => {
                    if (_.indexOf(id, line.product.id) !== -1) {
                        arr_before_product.push(line.product.id)
                    }
                });
                applies.forEach((apply) => {
                    // if (apply.product_id[0] === id[0]) {
                    if (apply.product_id[0] === arr_before_product[0]) {
                        if (apply.product_id) {
                            this.applyForProductGiftCondition(order, apply, conditions);
                        } else if (apply.category_id) {
                            this.applyForCategoryGiftCondition(order, apply, conditions);
                        }
                    }
                });
            }
            if (!this.x_promotion_apply_or) {
                applies.forEach((apply) => {
                    if (apply.product_id) {
                        this.applyForProductGiftCondition(order, apply, conditions);
                    } else if (apply.category_id) {
                        this.applyForCategoryGiftCondition(order, apply, conditions);
                    }
                });
            }
            conditions.forEach((condition) => {
                if (condition.product_id) {
                    this.setAppliedQuantityProductGiftCondition(order, condition)
                } else if (condition.category_id) {
                    this.setAppliedQuantityCategoryGiftCondition(order, condition)
                }
            })
            order.save_to_db()
        },
        applyForProductGiftCondition: function (order, apply, conditions) {
            // kiểm tra sản phẩm được tặng có trong đơn hàng không
            let conditionProductLine = []
            let number_used_promotion = [] //số lần sử dụng lũy kế
            let product = this.db.get_product_by_id(apply.product_id[0])
            let category_id = product.pos_categ_id[0]
            let applyOrderLines = this.getApplyOrderLines(order, apply, conditions, category_id, 'product')

            // tính lại số lượng các sản phẩm nếu trong đơn có các SP trùng nhau nhưng khác số lượng
            let orderProductQty = this.getOrderLineProductsQty(order, null)
            for (let product_id in orderProductQty) {
                conditions.forEach((condition) => {
                    //sản phẩm điều kiện = sản phẩm trong giỏ hàng & sl sản phẩm điều kiện >= sl san phẩm trong gio hang
                    // if (condition.product_id[0] === parseInt(product_id)) {
                    if (condition.product_id[0] === parseInt(product_id) && orderProductQty[product_id] >= condition.qty) {
                        number_used_promotion.push(Math.floor(orderProductQty[product_id] / condition.qty))
                        // conditionProductLine.push(line)
                    }
                })
            }
            // order.orderlines.forEach((line) => {
            //     conditions.forEach((condition) => {
            //         if (condition.product_id[0] === line.product.id) {
            //             number_used_promotion.push(Math.floor(line.quantity / condition.qty))
            //             // number_used_promotion.push(line.quantity % condition.qty)
            //             conditionProductLine.push(line)
            //         }
            //     })
            // })
            if (this.x_accumulate) {
                // lấy max số lượng lũy kế dựa trên sản phẩm điều kiện (phải thoản mãn)
                let max_number_allow_accumulate = Math.max(...number_used_promotion)
                this.createUpdateApplyOrderLine(order, apply, product, applyOrderLines, max_number_allow_accumulate);
            }
            if (!this.x_accumulate) {
                this.createUpdateApplyOrderLineNotAccumlate(order, apply, product, applyOrderLines);
            }
            // this.addProductApplyOrder(apply.qty, order, product, false);
        },

        applyForCategoryGiftCondition: function (order, apply, conditions) {
            let category_id = apply.category_id[0]
            let applyOrderLines = this.getApplyOrderLines(order, apply, conditions, category_id, 'category')
            // lấy sản phẩm có giá trị lớn nhất
            let productMostExepensiveByCategory = this.getMostExpensiveProductByCategory(apply, order)
            this.createUpdateApplyOrderLine(order, apply, productMostExepensiveByCategory, applyOrderLines)
            // this.addProductApplyOrder(apply.qty, order, productMostExepensiveByCategory, false);
        },

        getCategoryQty: function (order, category_id, conditions) {
            let conditionCategoryLineQty = 0
            conditions.forEach((condition) => {
                if (condition.category_id && condition.category_id[0] === category_id) {
                    conditionCategoryLineQty += condition.qty
                } else if (condition.product_id) {
                    let conditionProduct = this.db.get_product_by_id(condition.product_id[0])
                    if (conditionProduct) {
                        if (conditionProduct.pos_categ_id[0] === category_id) {
                            conditionCategoryLineQty += condition.qty
                        }
                    }
                }
            })
            let orderCategoryLineQty = 0
            order.orderlines.forEach((line) => {
                if (line.product.pos_categ_id[0] === category_id) {
                    orderCategoryLineQty += line.quantity
                }
            })
            return [conditionCategoryLineQty, orderCategoryLineQty]
        },

        getApplyOrderLines: function (order, apply, conditions, category_id, type) {
            let [conditionCategoryLineQty, orderCategoryLineQty] = this.getCategoryQty(order, category_id, conditions)
            // if (orderCategoryLineQty === conditionCategoryLineQty) {
            //     return []
            // }
            // else {}
            // fix điều kieejnn áp dụng với 1 sp trong đk CTKM
            if (type == 'category') {
                return order.orderlines.filter((line) => {
                    let validLine = line.product.pos_categ_id[0] === category_id && !line.promotion_id
                    if (!validLine) {
                        return false
                    }
                    let conditionProductLine = conditions.filter(condition => condition.product_id[0] === line.product.id)
                    if (!conditionProductLine.length) {
                        return true
                    }
                    let conditionQty = 0
                    conditionProductLine.forEach((condition) => {
                        conditionQty += condition.qty
                    })
                    return conditionQty > line.quantity;
                }).sort(function (first, second) {
                    return second.price - first.price;
                });
            } else if (type == 'product') {
                return order.orderlines.filter((line) => {
                    let conditionQuantity = 0
                    let conditionProductLine = conditions.filter(condition => condition.product_id[0] === line.product.id)
                    if (conditionProductLine.length) {
                        conditionQuantity = conditionProductLine[0].qty
                    }
                    return line.product.id === apply.product_id[0] && !line.promotion_id && (conditionQuantity + apply.qty <= line.quantity)
                }).sort(function (first, second) {
                    return second.quantity - first.quantity;
                });
            } else {
                return []
            }

        },

        createUpdateApplyOrderLineNotAccumlate: function (order, apply, product, applyOrderLines) {
            if (applyOrderLines.length < 1) {
            } else {
                // áp dụng promotion khi có sản phẩm trong đơn
                let apply_qty = apply.qty;
                applyOrderLines.forEach((line) => {
                    if (apply_qty !== 0) {
                        if (line.quantity > apply_qty) {
                            line.set_quantity(line.quantity - apply_qty);
                            this.addProductApplyOrder(apply_qty, order, line, false);
                            apply_qty = 0
                        } else {
                            line.set_discount(100);
                            line.setPromotion(apply.promotion_id[0])
                            apply_qty = apply_qty - line.quantity
                        }
                    }
                })
                // trường hợp số lượng sản phẩm trong đơn nhỏ hơn số lượng được áp dụng => tạo thêm phần dư
                if (apply_qty !== 0) {
                    this.addProductApplyOrder(apply_qty, order, product, true);
                }
            }

        },
        createUpdateApplyOrderLine: function (order, apply, product, applyOrderLines, number_used_promotion) {
            if (applyOrderLines.length < 1) {
                // áp dụng promotion khi không có sản phẩm trong đơn

                // thêm điều kiện hoặc trong mua hàng tặng hàng
                // this.addProductApplyOrder(apply.qty, order, product, false);
            } else {
                // áp dụng promotion khi có sản phẩm trong đơn
                let apply_qty = apply.qty;
                applyOrderLines.forEach((line) => {
                    let check = 0
                    if (apply_qty !== 0) {
                        if (line.quantity === apply_qty * number_used_promotion) {
                            line.set_discount(100);
                            line.setPromotion(apply.promotion_id[0])
                            apply_qty = 0
                            check += 1
                        }
                        if (line.quantity > apply_qty * number_used_promotion && check === 0) {
                            line.set_quantity(line.quantity - apply_qty * number_used_promotion);
                            this.addProductApplyOrder(apply_qty * number_used_promotion, order, line, false);
                            apply_qty = 0
                            check += 1
                        }
                        if (line.quantity === apply_qty && check === 0) {
                            line.set_discount(100);
                            line.setPromotion(apply.promotion_id[0])
                            apply_qty = apply_qty - line.quantity
                            check += 1
                        }
                        if (line.quantity < apply_qty * number_used_promotion && check === 0) {
                            line.set_discount(100);
                            line.setPromotion(apply.promotion_id[0])
                            apply_qty = 0
                            check += 1
                        }
                        if (check === 0) {
                            line.set_quantity(line.quantity - apply_qty);
                            this.addProductApplyOrder(apply_qty, order, line, false);
                            apply_qty = 0
                        }

                    }
                })
                // trường hợp số lượng sản phẩm trong đơn nhỏ hơn số lượng được áp dụng => tạo thêm phần dư
                if (apply_qty !== 0) {
                    this.addProductApplyOrder(apply_qty, order, product, true);
                }
            }
        },

        setAppliedQuantityProductGiftCondition: function (order, condition) {
            let conditionOrderLine = order.orderlines.filter(line => line.product.id === condition.product_id[0] && !line.promotion_id)
            this.setAppliedQuantityGiftCondition(conditionOrderLine, condition)
        },

        setAppliedQuantityCategoryGiftCondition: function (order, condition) {
            let conditionOrderLine = order.orderlines.filter(line => line.product.pos_categ_id[0] === condition.category_id[0] && !line.promotion_id)
            this.setAppliedQuantityGiftCondition(conditionOrderLine, condition)
        },

        setAppliedQuantityGiftCondition: function (conditionOrderLine, condition) {
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

        addProductApplyOrder: function (quantity, order, line, merge) {
            // let product = this.db.get_product_by_id(line.product.id);
            let product = line.product;
            let options = {
                // price: 0,
                price: line.price,
                quantity: quantity,
                discount: 100,
                merge: merge,
                extras: {
                    promotion_id: this.id
                },
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
            // order.orderlines.filter(line => line.promotion_id === this.id).forEach((line) => {
            //     line.apply_promotion_for_line_ids = this.getConditionOrderLine(order)
            // })
        },

        getConditionOrderLine: function (order) {
            let conditions = this.db.getPromotionGiftConditionByPromotionIds([this.id])
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

        getMostExpensiveProductByCategory: function (apply, order) {
            var pricelist = order.pricelist;
            let productInCategory = this.db.product_by_category_id[apply.category_id[0]]
            let productInCategoryObj = []
            productInCategory.forEach((product) => {
                productInCategoryObj.push(this.db.get_product_by_id(product))
            })
            return productInCategoryObj.sort(function (first, second) {
                return second.get_price(pricelist, apply.qty) - first.get_price(pricelist, apply.qty);
            })[0];
        },

        revertAppliedOnOrder: function (order) {
            Promotion.prototype.revertAppliedOnOrder.call(this, order);
            if (this.type !== 'gift_condition' || !order.orderlines) {
                return;
            }
            // revert promotion applied quantity in condition order line
            let conditionOrderLine = this.getConditionOrderLine(order)
            order.orderlines.filter(line => conditionOrderLine.includes(line.id)).forEach((line) => {
                // Fix when clear promotion;
                if (!line) return;
                line.promotion_applied_quantity = 0
            });
            //Clear all applied order of promotion
            let product_promotion = []
            order.orderlines.filter((orderline) => {
                return orderline.getPromotionId() === this.id
            }).forEach((line) => {
                // Fix when clear promotion;
                if (!line) return;
                line.set_unit_price(line.product.get_price(order.pricelist, line.quantity));
                line.set_discount(0);
                line.promotion_id = undefined
                product_promotion.push(line.product.id)
                // line.apply_promotion_for_line_ids = []
            });
            var map_product = new Map()
            product_promotion.forEach((product) => {
                let count = 0
                order.orderlines.filter((line) => {
                    if (line.product.id === product) {
                        count += line.quantity
                    }
                })
                map_product.set(product, count)
            })
            let product_insert = []
            order.orderlines.filter((line) => {
                if (map_product.get(line.product.id) || map_product.get(line.product.id) === 0){
                    if (product_insert.indexOf(line.product.id) === -1) {
                        product_insert.push(line.product.id)
                    }
                }
            })
            product_insert.forEach((product) => {
                var combo_prod_detail = []
                order.orderlines.filter((orderline) => {
                    return orderline.product.id === product
                }).forEach((line) => {
                    combo_prod_detail.push(line.combo_prod_info)
                    order.remove_orderline(line);
                })
                let product_add = this.db.get_product_by_id(product)
                order.add_product(product_add, {
                    quantity: map_product.get(product),
                });

                //Add lai combo detail
                order.orderlines.filter((orderline) => {
                    return orderline.product.id === product && orderline.product.x_is_combo
                }).forEach((line) => {
                    line.combo_prod_info = combo_prod_detail[0]
                    // line.set_combo_prod_info(combo_prod_detail);
                })
            })

        },

    });

    return models;

});
