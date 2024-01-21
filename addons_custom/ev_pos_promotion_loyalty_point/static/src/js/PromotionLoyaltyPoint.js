odoo.define('ev_pos_promotion_loyalty_point.Order', function (require) {
    "use strict"

    var models = require('point_of_sale.models');
    var core = require('web.core');
    var utils = require('web.utils');

    var round_pr = utils.round_precision;

    var _superOrder = models.Order;
    models.Order = models.Order.extend({
         initialize: function (attributes, options) {
            this.x_promotion_loyalty_point = options.x_promotion_loyalty_point || 0
            _superOrder.prototype.initialize.apply(this, arguments)
            return this
        },

        export_for_printing: function () {
            var json = _superOrder.prototype.export_for_printing.apply(this, arguments);
            if (this.pos.loyalty && this.get_client()) {
                json.loyalty.points_won = this.get_won_points() + this.get_points_promotion_loyalty()
            }
            return json;
        },

        set_x_promotion_loyalty_point: function(x_promotion_loyalty_point){
             this.x_promotion_loyalty_point = x_promotion_loyalty_point;
        },

        get_points_promotion_loyalty: function () {
            if (!this.pos.loyalty || !this.get_client()) {
                return 0;
            }

            return round_pr(this.x_promotion_loyalty_point, 1);
        },

        get_new_points: function () {
            if (!this.pos.loyalty || !this.get_client()) {
                return 0;
            } else {
                return round_pr(this.get_won_points() - this.get_spent_points() + this.get_points_promotion_loyalty(), 1);
            }
        },

        set_x_is_miniapp_member: function(is_miniapp_member){
             this.x_is_miniapp_member = is_miniapp_member;
        },

        set_x_note_member_app: function(note_member_app){
             this.x_note_member_app = note_member_app;
        },

        set_client: function(client){
            var order = this.pos.get_order()
			_superOrder.prototype.set_client.call(this, client);
            order.set_x_is_miniapp_member(order.is_created_by_api);
            order.set_x_note_member_app('')
		}

    });

    return models;

});
