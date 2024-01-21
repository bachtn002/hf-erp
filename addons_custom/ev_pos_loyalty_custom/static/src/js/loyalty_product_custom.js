odoo.define('ev_pos_loyalty_custom.Order', function (require) {
    "use strict"

    const models = require('point_of_sale.models');
    var core = require('web.core');
    var utils = require('web.utils');

    var round_pr = utils.round_precision;

    var _t = core._t;
    var _superOrder = models.Order;
    models.Order = models.Order.extend({
        get_won_points: function () {
            if (!this.pos.loyalty || !this.get_client()) {
                return 0;
            }
            var id_pos_loyalty = this.pos.loyalty.id
            var total_points = 0;
            for (var line of this.get_orderlines()) {
                if (line.get_reward()) {  // Reward products are ignored
                    continue;
                }

                var line_points = 0;
                this.pos.loyalty.rules.forEach(function (rule) {
                    var rule_points = 0
                    if (rule.loyalty_program_id[0] === id_pos_loyalty) {
                        if (rule.valid_product_ids.find(function (product_id) {
                            return product_id === line.get_product().id
                        })) {
                            rule_points += rule.points_quantity * line.get_quantity();
                            rule_points += rule.points_currency * line.get_price_with_tax();
                        }
                        if (rule_points > line_points)
                            line_points = rule_points;
                    }
                });

                total_points += line_points;
            }
            //tích điểm theo sản phẩm
            var total_points_product = 0;
            for (var line_product of this.get_orderlines()) {
                let product_id_test = line_product.get_product().id
                let product_quantity = line_product.get_quantity();
                if (line_product.get_reward()) {  // Reward products are ignored
                    continue;
                }
                var line_product_points = 0;
                this.pos.loyalty.rules.forEach(function (rule) {
                    var product_rule_ids = rule.product_rule_rule
                    if (rule.loyalty_program_id[0] === id_pos_loyalty) {
                        product_rule_ids.forEach((product_rule_id) => {
                            if (product_rule_id === product_id_test) {
                                line_product_points += rule.point_per_product * product_quantity;
                            }
                        });
                    }
                });
                total_points += line_product_points;

            }
            // tích điểm theo danh mục sản phẩm
            for (var line_product_cate of this.get_orderlines()) {
                let product_categ_id = line_product_cate.get_product().categ.id
                let product_quantity = line_product_cate.get_quantity();
                if (line_product.get_reward()) {  // Reward products are ignored
                    continue;
                }
                var line_product_categ_points = 0;
                this.pos.loyalty.rules.forEach(function (rule) {
                    var product_categ_rule_ids = rule.product_cate_rule_rule
                    if (rule.loyalty_program_id[0] === id_pos_loyalty) {
                        product_categ_rule_ids.forEach((product_categ_rule_id) => {
                            if (product_categ_rule_id === product_categ_id) {
                                line_product_categ_points += rule.point_per_product * product_quantity;
                            }
                        });
                    }
                });
                total_points += line_product_categ_points;
            }
            // total_points += line_product_categ_points;
            // tích điểm theo danh mục sản phẩm trên POS
            for (var line_product_catrgory of this.get_orderlines()) {
                var line_product_category_points = 0;
                let product_id_test = line_product_catrgory.get_product().id
                let product = line_product_catrgory.get_product()
                let product_quantity = line_product.get_quantity();
                this.pos.loyalty.rules.forEach(function (rule) {
                    var product_cate_ids = rule.category_id;
                    if (rule.loyalty_program_id[0] === id_pos_loyalty) {
                        product_cate_ids.forEach((product_cate_id) => {
                            if (product.pos_categ_id[0] === product_cate_id) {
                                line_product_category_points += rule.point_per_product * product_quantity;
                            }
                        });
                    }
                });
                total_points += line_product_category_points;
            }
            total_points += this.get_total_with_tax() * this.pos.loyalty.points;
            // check khách hàng không áp dụng
            let partner_not_applys = this.pos.loyalty.res_partner_id_not_apply
            if (_.indexOf(partner_not_applys, this.get_client().id) != -1) {
                total_points = 0
            }
            // check nhóm khách hàng không áp dụng
            let partner_group_not_applys = this.pos.loyalty.res_partner_id_not_apply_group
            if (_.indexOf(partner_group_not_applys, this.get_client().partner_groups[0]) != -1) {
                total_points = 0
            }
            // check là sàn thương mại điện tử
            if (this.get_client().x_ecommerce) {
                total_points = 0
            }
            // ko áp dụng KHTT theo điểm bán
            // let pos_config_applys = this.pos.loyalty.pos_config_apply
            // pos_config_applys.forEach((pos_config_id) => {
            //     if (pos_config_id === this.pos.config_id) {
            //         total_points = 0
            //     }
            // })
            return round_pr(total_points, 1);
        },

    });

    return models;

});
