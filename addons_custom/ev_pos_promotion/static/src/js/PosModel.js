odoo.define('ev_pos_promotion.PosModel', function (require) {
    "use strict"

    const models = require('ev_pos_promotion.models');

    let PosModel = models.PosModel;
    models.PosModel = PosModel.extend({
        prepare_id_product_domain: function(search_key, load_data){
            return ['&', '&', ['sale_ok','=',true],['available_in_pos','=',true], ['id','=', search_key]]
        },
        search_product_by_id_to_server: function(search_key){
            var self = this;
            return new Promise(function (resolve, reject) {
                var fields = _.find(self.models, function(model){ return model.model === 'product.product'; }).fields;
                var domain = self.prepare_id_product_domain(search_key);
                self.rpc({
                    model: 'product.product',
                    method: 'search_read',
                    args: [domain, fields, 0, 10],
                }, {
                    timeout: 3000,
                    shadow: true,
                })
                .then(function (products) {
                    if(products.length > 0){
                        var using_company_currency = self.config.currency_id[0] === self.company.currency_id[0];
                        var conversion_rate = self.currency.rate / self.company_currency.rate;
                        self.db.add_products(_.map(products, function (product) {
                            if (!using_company_currency) {
                                product.lst_price = round_pr(product.lst_price * conversion_rate, self.currency.rounding);
                            }
                            product.categ = _.findWhere(self.product_categories, {'id': product.categ_id[0]});
                            product.pos = self;
                            return new models.Product({}, product);
                        }));
                        resolve();
                    } else {
                        reject('Product does not exist!');
                    }
                }, function (type, err) { reject(); });
            });
        },
        /**
         * getPromotions
         *
         * Lấy về toàn bộ Promotions đã được load
         *
         */
        getPromotions: function () {
            // Lấy toàn bộ promotion phù hợp với điểm bán lẻ đang được lưu trên localStore
            let rows = this.db.load('promotions');
            // Chuyển đổi promotion tự json -> Promotion object
            let promotions = [];
            rows.forEach((row) => {
                let promotion = new models.Promotion(row, {
                    db: this.db,
                    pos: this.pos,
                });
                promotions.push(promotion);
            });
            return promotions;
        },

        /**
         * getValidPromotions
         *
         * Trả về danh sách promotions phù hợp với đơn hàng
         *
         * @param {} order
         */
        getValidPromotions: function (order = null, show = false) {
            // Hàm lấy danh sách khuyến mãi mà đơn hàng thoả mãn điều kiện.
            order = order || this.get_order();
            if (order.orderlines.length < 1) {
                return [];
            }
            let promotions = this.getPromotions();
            return promotions.filter((item) => {
                return item.isValidOrder(order, show);
            });
        },

        /**
         * applyPromotions
         *
         * Áp dụng danh sách promotion vào đơn hàng
         *
         * @param {} promotions
         * @param {} order
         */
        applyPromotions: async function (promotions, order = null) {
            order = order || this.get_order();
            let ordersAppliedPromotions = this.getOrderAppliedPromotions();
            if (!ordersAppliedPromotions.hasOwnProperty(order.uid)) {
                ordersAppliedPromotions[order.uid] = [];
            }
            let data = ordersAppliedPromotions[order.uid].concat(promotions);
            let duplicateIds = [];
            data = data.filter((item) => {
                return _.indexOf(duplicateIds, item.id) === -1;
            });

            // Xắp xếp lại promotion theo thứ tự
            ordersAppliedPromotions[order.uid] = this.sortPromotions(data);

            // Lưu list promotion áp dụng cho đơn hàng
            // Và áp dụng theo trình tự đã sắp xếp
            this.saveOrderAppliedPromotions(ordersAppliedPromotions);
            data.forEach((item) => {
                item.applyPromotionToOrder(order);
            });
             // Bỏ giảm trừ điểm tích lũy sau khi áp dụng promotion
            order.orderlines.forEach((line) => {
                if (line) {
                    if (line.reward_custom_id === 'reward') {
                        order.remove_orderline(line);
                    }
                }
            });
        },

        /**
         * applyPromotions
         *
         * Áp dụng danh sách promotion code vào đơn hàng
         *
         * @param {} promotions
         * @param {} order
         */
        applyPromotionsCode: function (promotions, order = null) {
            order = order || this.get_order();
            let ordersAppliedPromotions = this.getOrderAppliedPromotions();
            if (!ordersAppliedPromotions.hasOwnProperty(order.uid)) {
                ordersAppliedPromotions[order.uid] = [];
            }
            let data = ordersAppliedPromotions[order.uid].concat(promotions);
            ordersAppliedPromotions[order.uid] = this.sortPromotions(data);
            // Lưu list promotion áp dụng cho đơn hàng
            // Và áp dụng theo trình tự đã sắp xếp
            this.saveOrderAppliedPromotions(ordersAppliedPromotions);
            promotions.applyPromotionToOrder(order);
            // Bỏ giảm trừ điểm tích lũy sau khi áp dụng promotion code
            order.orderlines.forEach((line) => {
                if (line) {
                    if (line.reward_custom_id === 'reward') {
                        order.remove_orderline(line);
                    }
                }
            });
        },

        /**
         * getPromotionById
         *
         * Lấy về promotion bằng id
         *
         * @param {} id
         */
        getPromotionById: function (id) {
            let promotions = this.getPromotions();
            let res = promotions.filter((item) => {
                return item.id === id;
            });
            if (res.length > 0)
                return res[0];
            return {};
        },

        /**
         * getPromotionsApplied
         *
         * Trả về danh sách promotion đã áp dụng cho đơn hàng
         *
         * @param {} order
         */
        getPromotionsApplied: function (order = null) {
            // Lấy các khuyến mãi đã áp dụng cho đơn hàng
            order = order || this.get_order();
            let ordersAppliedPromotions = this.getOrderAppliedPromotions();
            if (ordersAppliedPromotions.hasOwnProperty(order.uid)) {
                return ordersAppliedPromotions[order.uid];
            }
            return [];
        },

        /**
         * removePromotionsApplied
         *
         * Xoá toàn bộ promotion đã được áp dụng vào đơn hàng
         *
         * @param {} order
         */
        removePromotionsApplied: function (order = null) {
            //Xoá toán bộ khuyến mãi đã đáp dụng
            order = order || this.get_order();
            let orderline = order.get_orderlines();
            for(var i = 0; i < orderline.length; i++){
                var line = orderline[i];
                if(typeof line.x_is_price_promotion != undefined){
                    line.x_is_price_promotion = 0;
                }
                if(typeof line.x_product_promotion != undefined){
                    line.x_product_promotion = '';
                }
                if(typeof line.amount_promotion_loyalty != undefined){
                    line.amount_promotion_loyalty = 0;
                }
                if(typeof line.amount_promotion_total != undefined){
                    line.amount_promotion_total = 0;
                }
            }
            let ordersAppliedPromotions = this.getOrderAppliedPromotions();
            if (ordersAppliedPromotions.hasOwnProperty(order.uid)) {
                // Hoàn trả lại toàn bộ nhưng gì đã áp dụng vào đơn hàng của promotion
                ordersAppliedPromotions[order.uid].forEach((item) => {
                    item.revertAppliedOnOrder(order);
                });
            }
            ordersAppliedPromotions[order.uid] = [];
            this.saveOrderAppliedPromotions(ordersAppliedPromotions)
        },

        /**
         * getOrderAppliedPromotions
         *
         * Trả về danh sách dữ liệu promotion được áp dụng vào đơn hàng
         * theo từng đơn hàng dự vào uid của đơn hàng
         *
         */
        getOrderAppliedPromotions: function () {
            let promotions = this.db.load('orders_applied_promotions', {});
            Object.entries(promotions).forEach(([uid, rows]) => {
                // Chuyển đổi json -> Promotion object
                promotions[uid] = rows.map((item) => {
                    return new models.Promotion(item, {
                        db: this.db,
                        pos: this.pos,
                    });
                });
            });
            return promotions;
        },

        /**
         * saveOrderAppliedPromotions
         *
         * Lưu danh sách promotion áp dụng vào đơn hàng
         *
         * @param {} promotions
         */
        saveOrderAppliedPromotions: function (promotions) {
            Object.entries(promotions).forEach(([uid, rows]) => {
                promotions[uid] = rows.map((item) => {
                    return item.toJSON({selected: item.selected});
                });
            })
            this.db.save('orders_applied_promotions', promotions);
        },

        sortPromotions: function (promotions) {
            // Sort by priority;
            promotions.sort(function (promotionA, promotionB) {
                let x = promotionA.priority;
                let y = promotionB.priority;
                let x_id = promotionA.id;
                let y_id = promotionB.id;
                let compare = ((x < y) ? -1 : ((x > y) ? 1 : 0))
                if (compare === 0) {
                    return x_id - y_id
                } else {
                    return compare
                }
            });
            return promotions;
        },

    });

    return models;

});
