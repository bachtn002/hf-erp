odoo.define('ev_pos_promotion_game_total_amount.OrderLine', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var core = require('web.core');
    var utils = require('web.utils');

    var round_pr = utils.round_precision;

    var _t = core._t;

    models.load_fields('pos.order', ['x_game_turn_reward']);
    models.load_fields('pos.promotion', ['game_code']);

    models.load_models([{
    model: 'pos.promotion.game.total.amount',
    label: 'Promotion Game Total Amount',
    fields: ['promotion_id', 'game_turn', 'total_amount', 'game_code'],
    domain: (self) => {
        return [['promotion_id', 'in', self.db.getPromotionIds()]]
    },
    loaded: (self, res) => {
        self.game_return_programs = res;
        // self.total_game_turn_reward = 0;
        self.db.addPromotionGameTotalAmount(res);
    }
    }], {after: 'pos.promotion'});


    var OrderSupper = models.Order;
    models.Order = models.Order.extend({

        initialize: function (attributes, options) {
            this.x_game_turn_reward = options.x_game_turn_reward || 0;
            this.x_game_turn_rules = options.x_game_turn_rules || [];
            OrderSupper.prototype.initialize.apply(this, arguments);
            return this;
        },

        init_from_JSON: function (json) {
            this.x_game_turn_reward = json.x_game_turn_reward;
            this.x_game_turn_rules = json.x_game_turn_rules;
            OrderSupper.prototype.init_from_JSON.call(this, json);
        },

        export_as_JSON: function () {
            var json = OrderSupper.prototype.export_as_JSON.apply(this, arguments);
            json.x_game_turn_reward = this.get_x_game_turn_reward();
            json.x_game_turn_rules = this.get_x_game_turn_rules();
            return json;
        },
        export_for_printing: function () {
            let res = OrderSupper.prototype.export_for_printing.apply(this, arguments);
            res.x_game_turn_reward = this.get_x_game_turn_reward();
            res.x_game_turn_rules = this.get_x_game_turn_rules();
            return res;
        },

        set_x_game_turn_reward: function (x_game_turn_reward) {
            if(x_game_turn_reward === 0){
                this.x_game_turn_reward = x_game_turn_reward;
            }else{
                //cộng dồn lượt chơi trường hợp có nhiều CTKM
                this.x_game_turn_reward += x_game_turn_reward;
            }
        },
        get_x_game_turn_reward: function () {
            return this.x_game_turn_reward;
        },

        set_x_game_turn_rules: function (x_game_turn_rules) {
            // lưu rule áp dụng tích lượt chơi
            if(x_game_turn_rules.length === 0){
                this.x_game_turn_rules = x_game_turn_rules;
            }else{
                this.x_game_turn_rules.push(x_game_turn_rules);
            }
        },
        get_x_game_turn_rules: function () {
            return this.x_game_turn_rules;
        },

    });
    return models;

});
