odoo.define('ev_pos_promotion_gift_code.models', function (require) {
    "use strict"

    let models = require('point_of_sale.models');

    models.load_models([{
        model: 'pos.promotion.gift.code.total.amount',
        label: 'Promotion Gift Code Total Amount',
        fields: ['promotion_id', 'promotion_code_id', 'total_amount'],
        domain: (self) => {
            return [['promotion_id', 'in', self.db.getPromotionIds()]]
        },
        loaded: (self, res) => {
            self.promotion_return_gift_code = res;
            self.db.addPromotionGiftCodeTotalAmount(res);
        }
    }], {after: 'pos.promotion'});

    let order = models.Order;
    models.Order = models.Order.extend({

        initialize: function (attributes, options) {
            this.x_name_promotion = options.x_name_promotion || [];      //x_name_promotion: Tên CTKM được tặng
            this.x_base64_image = options.x_base64_image || 0;
            this.list_code_gave_away = options.list_code_gave_away || [];
            this.rules_valid = options.rules_valid || [];
            order.prototype.initialize.apply(this, arguments);
            return this;
        },

        init_from_JSON: function (json) {
            this.x_name_promotion = json.x_name_promotion;
            this.x_base64_image = json.x_base64_image;
            this.list_code_gave_away = json.list_code_gave_away;
            this.rules_valid = json.rules_valid || [];
            order.prototype.init_from_JSON.call(this, json);
        },

        export_as_JSON: function () {
            let json = order.prototype.export_as_JSON.apply(this, arguments);
            json.x_name_promotion = this.get_x_name_promotion();
            json.x_base64_image = this.x_base64_image;
            json.list_code_gave_away = this.get_code_gave_away();
            json.rules_valid = this.get_rules_valid();
            return json;
        },

        export_for_printing: function () {
            let res = order.prototype.export_for_printing.apply(this, arguments);
            res.x_name_promotion = this.get_x_name_promotion();
            res.x_base64_image = this.x_base64_image;
            res.list_code_gave_away = this.get_code_gave_away();
            return res;
        },

        set_code_gave_away: function (data) {
            if (data.length > 0 && this.list_code_gave_away.length === 0){
                this.list_code_gave_away.push(data[0]);
            }
        },

        get_code_gave_away: function () {
            return this.list_code_gave_away;
        },

        set_rules_valid: function (rule) {
            let promotion_in_rule = []
            this.rules_valid.forEach((promo) => {
                promotion_in_rule.push(
                    promo['promotion_id'].toString() + promo['pos_promotion_id'].toString())
            })
            if (rule.length > 0) {
                rule.forEach((line) => {
                    let promotions_key = line.promotion_id.toString() + line.pos_promotion_id.toString()
                    if (!promotion_in_rule.includes(promotions_key)) {
                        this.rules_valid.push({
                            'promotion_id': line.promotion_id,
                            'pos_promotion_id': line.pos_promotion_id,
                            'number_code_give': line.number_code_give //tặng 1 code trên 1 CTKM
                        })
                    }
                })
            } else {
                this.rules_valid = []
            }
        },

        get_rules_valid: function () {
            return this.rules_valid;
        },

        set_x_name_promotion: function (data) {
            if (data.length !== 0) {
                this.x_name_promotion.push(data);
            } else {
                this.x_name_promotion = data
            }
        },

        get_x_name_promotion: function () {
            return this.x_name_promotion;
        },

    })
    return models;
});