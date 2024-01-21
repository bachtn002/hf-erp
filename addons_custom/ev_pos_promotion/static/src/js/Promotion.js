odoo.define('ev_pos_promotion.Promotion', function (require) {
    "use strict"

    const models = require('point_of_sale.models');
    const FieldUtils = require('web.field_utils');

    const SELECT_ICON = 'fa fa-circle';
    const UNSELECT_ICON = 'fa fa-circle-thin';
    const rpc = require('web.rpc');

    models.Promotion = Backbone.Model.extend({
        /**
         * initialize
         *
         * Khởi tạo Promotion
         *
         * @param {} attr
         * @param {} options
         */
        initialize: function (promotionJson, options) {
            Backbone.Model.prototype.initialize.call(this, arguments);
            this.db = options.db;
            this.pos = options.pos;
            if (promotionJson) {
                try {
                    this.id = promotionJson.id;
                    this.name = promotionJson.name;

                    for (let [key, value] of Object.entries(promotionJson)) {
                        this[key] = value;
                    }

                } catch (e) {
                    console.error('ERROR: promotion init from json', promotion);
                }
            }
            this.selected = false;
            this.buildSelectIcon();
        },

        /**
         * initFromJson
         *
         * Khởi tạo promotion từ dữ liệu json
         *
         * @param {} json
         */
        initFromJson: function (json) {
            this.name = json.name;
            this.start_date = json.start_date;
            this.end_date = json.end_date;
            this.start_time = json.start_time;
            this.end_time = json.end_time;
            this.company_id = json.company_id;
            this.type = json.type;
            this.partner_groups = json.partner_groups;
            this.partner_groups_not = json.partner_groups_not;
            this.priority = json.priority;
            this.product_id = json.product_id;
            this.partner_ids_without_group = json.partner_ids_without_group;
        },

        /**
         * exportFromJson
         *
         * Convert Promotion object to json
         *
         */
        exportToJson: function () {
            let json = {
                id: this.id,
                name: this.name,
                start_date: this.start_date,
                end_date: this.end_date,
                start_time: this.start_time,
                end_time: this.end_time,
                company_id: this.company_id,
                type: this.type,
                partner_groups: this.partner_groups,
                partner_groups_not: this.partner_groups_not,
                priority: this.priority,
                product_id: this.product_id,
                selected: this.selected,
                icon: this.icon,
                partner_ids_without_group: this.partner_ids_without_group,
            };
            return json;
        },

        toJSON: function (options) {
            let obj = Backbone.Model.prototype.toJSON.call(this, arguments);
            return {...obj, ...options};
        },

        /**
         * isValidOrder
         *
         * Hàm kiểm tra promotion có áp dụng được cho đơn hàng không
         *
         * @param {} order
         * @param show
         */
        isValidOrder: function (order, show) {
            //TODO
        },

        /**
         * applyPromotionToOrder
         *
         * Hàm áp dụng promotion vào đơn hàng
         *
         * @param {} order
         */
        applyPromotionToOrder: function (order) {
            //TODO
            order = order || this.get_order();
            const orderlines = order.orderlines;
            // xóa giá phân bổ khi xóa CTKM
//            orderlines.forEach((line) => {
//                if (typeof(line.x_is_price_promotion) != "undefined"){
//                    line.x_is_price_promotion = undefined;
//                }
//                if (typeof(line.x_product_promotion) != "undefined"){
//                    line.x_product_promotion = undefined;
//                }
//            })
        },


        /**
         * revertAppliedOnOrder
         *
         * Hoàn trả các áp dụng của promotion hiện tại cho đơn hàng
         *
         * @param {} order
         */
        revertAppliedOnOrder: function (order) {
            //TODO
        },

        toggleSelect: function () {
            this.selected = !this.selected;
            this.buildSelectIcon();
        },

        setSelect: function (selected = false) {
            this.selected = selected;
            this.buildSelectIcon();
        },

        buildSelectIcon: function () {
            this.icon = this.selected ? SELECT_ICON : UNSELECT_ICON;
        },

        getOrderLineProductsQty: function (order = null, show) {
            let lineProductsQty = {};
            order.orderlines.forEach((line) => {
                // let quantity = line.quantity - line.getAppliedPromotionQuantity(show)
                let quantity = line.quantity
                if (lineProductsQty.hasOwnProperty(line.product.id)) {
                    lineProductsQty[line.product.id] += quantity
                } else {
                    lineProductsQty[line.product.id] = quantity
                }
            });
            return lineProductsQty;
        },

        getOrderLineCategoriesQty: function (order = null, show) {
            let lineCategoriesQty = {};
            order.orderlines.forEach((line) => {
                let line_category_id = line.product.pos_categ_id[0]
                let quantity = line.quantity - line.getAppliedPromotionQuantity(show)
                if (lineCategoriesQty.hasOwnProperty(line_category_id)) {
                    lineCategoriesQty[line_category_id] += quantity
                } else {
                    lineCategoriesQty[line_category_id] = quantity
                }
            });
            return lineCategoriesQty;
        },

        getConditionCategoryQty: function (conditions) {
            let orderCategoryQty = {};
            conditions.forEach((condition) => {
                if (condition.product_id) {
                    let product = this.db.get_product_by_id(condition.product_id[0])
                    // fix lỗi sản phẩm không có trong cửa hàng k load được pos_categ_id
                    if (product) {
                        if (orderCategoryQty.hasOwnProperty(product.pos_categ_id[0])) {
                            orderCategoryQty[product.pos_categ_id[0]] += condition.qty
                        } else {
                            orderCategoryQty[product.pos_categ_id[0]] = condition.qty
                        }
                    }
                }
                if (condition.category_id) {
                    if (orderCategoryQty.hasOwnProperty(condition.category_id[0])) {
                        orderCategoryQty[condition.category_id[0]] += condition.qty
                    } else {
                        orderCategoryQty[condition.category_id[0]] = condition.qty
                    }
                }
            });

            return orderCategoryQty;
        },
        isValidPartnerNot: function (order) {
            let partner_groups_not_in_promotion = this.partner_groups_not;
            // áp dụng CTKM ở điểm bán
            var pos_configs = this.pos_configs;
            var pos_config_current = order.pos.config_id;
            if (!this.apply_all_pos_config && !this.apply_manual_pos_config) {
                return false
            }
            if (!this.apply_all_pos_config) {
                if (!pos_configs.includes(pos_config_current)) {
                    return false
                }
            }

            // khách hàng trong đơn hàng
            let partnerInOrder = order.get_client();
            if (typeof partner_groups_not_in_promotion != 'undefined') {
                if (partnerInOrder) {
                    for (var i = 0; i < partnerInOrder.partner_groups.length; i++) {
                        for (var j = 0; j < partner_groups_not_in_promotion.length; j++) {
                            if (partnerInOrder.partner_groups[i] == partner_groups_not_in_promotion[j]) {
                                return false;
                            }
                        }
                    }
                }
            }
            // danh sách khách hàng ko áp dụng CTKM
            let partnerInPromotion = this.x_partner_not_ids;

            if (this.apply_all_res_partner_not_apply) {
                return false
            }
            if (!this.apply_all_res_partner_not_apply && !this.apply_manual_res_partner_not_apply) {
                return true
            }

            if (partnerInPromotion.length > 0) {
                // nếu không có khách hàng trong đơn hàng thì áp dụng
                if (!partnerInOrder) {
                    return true;
                }
                if (!partnerInPromotion.includes(partnerInOrder.id)) {
                    return true;
                }
                return false;
            }
            return true;
        },
        isValidPartner: function (order) {
            // áp dụng CTKM với đk áp dụng tất cả KH
            // if (!this.apply_all_res_partner_apply && !this.apply_manual_res_partner_apply) {
            //     return false
            // }
            // if (this.apply_all_res_partner_apply) {
            //     return true;
            // }
            let partnerInOrder = order.get_client();
            let partnerInPromotion = this.partner_ids;
            let partnerNotInPromotion = this.partner_ids_not;
            let partnerInPromotionFromGroup = this.partner_ids_without_group;
            let partner_groups_in_promotion = this.partner_groups
            let partner_groups_not_in_promotion = this.partner_groups_not
            // áp dụng với tất cả các khách hàng khi chọn áp dụng tất cả
            // if (this.apply_all_res_partner_apply) {
            //     return true;
            // }

            if (typeof this.partner_groups != 'undefined') {
                if (partnerInOrder) {
                    for (var i = 0; i < partnerInOrder.partner_groups.length; i++) {
                        for (var j = 0; j < this.partner_groups.length; j++) {
                            if (partnerInOrder.partner_groups[i] == this.partner_groups[j]) {
                                return true;
                            }
                        }
                    }
                }
            }

            // if (partnerInPromotion.length > 0) {
            //     if (!partnerInOrder) {
            //         return false;
            //     }
            //     if (partnerInPromotion.includes(partnerInOrder.id)) {
            //         return true
            //     }
            // }
            if (partnerNotInPromotion.length > 0) {
                if (!partnerInOrder) {
                    // return false
                    return true
                }
                if (partnerNotInPromotion.includes(partnerInOrder.id)) {
                    return false
                }
            }
            // áp dụng CTKM với đk áp dụng tất cả KH
            if (!this.apply_all_res_partner_apply && !this.apply_manual_res_partner_apply) {
                return false;
            }
            if (this.apply_all_res_partner_apply) {
                return true;
            }
            if (partnerInPromotionFromGroup.length > 0) {
                if (!partnerInOrder) {
                    return false;
                }
                if (!partnerInPromotionFromGroup.includes(partnerInOrder.id)) {
                    return false
                }
                return true;
            }
            if (partner_groups_in_promotion.length > 0) {
                return false
            }
            return true
        },
        isValidTime: function () {
            let now = new Date();
            let time = FieldUtils.parse.float_time(moment(now).format('HH:mm'));
            if (this.start_time && this.end_time && (time < this.start_time || time > this.end_time)) {
                return false
            }
            let day_week = this.vaction_ids; // lấy điều kiện thứ áp dụng CTKM
            let day_gets = this.db.getDays() //lấy danh sách các thứ trong models
            // Khai báo đối tượng Date
            var date = new Date();

            // Lấy số thứ tự của ngày hiện tại
            var current_day = date.getDay();
            let check_date = false
            //nếu không chọn thứ thì mặc định áp dụng CTKM tất cả ngày trong tuần
            if (day_week.length === 0) {
                return true
            }
            day_week.forEach((day) => {
                day_gets.forEach((day_get) => {
                    if (day === day_get.id) {
                        if (current_day === day_get.code) {
                            check_date = true;
                        }
                    }
                });
            });
            // return true
            return check_date;
        },
    });

    return models;

});
