odoo.define('ev_pos_loyalty_ui.PointsCounter', function (require) {
    "use strict"

    const core = require('web.core');
    const Counter = require('pos_loyalty.PointsCounter');
    const Registries = require('point_of_sale.Registries');

    const _t = core._t;

    class PointsCounter extends Counter {
        get_total_before() {
            return Counter.prototype.get_points_total.call(this)
            // return this.env.pos.get_order().get_client().loyalty_points
        }

        get_total_before_if_spent() {
            let total = Counter.prototype.get_points_total.call(this);
            let spent = Counter.prototype.get_points_spent.call(this);
            return total - spent;
        }

        get_points_total_if_spent() {
            let total_user = this.env.pos.get_order().get_client().loyalty_points
            let spent = Counter.prototype.get_points_spent.call(this);
            return total_user - spent;
        }

        get_points_total() {
            var self = this;
            let id = this.env.pos.get_order().get_client().id
            let args = [id, id];
            this.rpc({
                model: 'res.partner',
                method: 'search_loyalty_points',
                args: args,
            }, {
                timeout: 3000,
                shadow: true,
            })
                .then(function (loyalty_points) {
                    var client = self.env.pos.get_order().get_client();
                    if (client) {
                        client.loyalty_points = loyalty_points;
                    }
                });

            // let total = Counter.prototype.get_points_total.call(this);
            // let won = Counter.prototype.get_points_won.call(this);
            // let spent = Counter.prototype.get_points_spent.call(this);
            // return total - won + spent;
            return self.env.pos.get_order().get_client().loyalty_points
        }
    }

    Registries.Component.add(PointsCounter);

    return PointsCounter;

});
