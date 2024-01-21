odoo.define('ev_pos_promotion_loyalty_point.PointsCounter', function (require) {
    "use strict"

    const core = require('web.core');
    const Counter = require('ev_pos_loyalty_ui.PointsCounter');
    const Registries = require('point_of_sale.Registries');

    const _t = core._t;
    var utils = require('web.utils');

    var round_pr = utils.round_precision;

    class PointsCounter extends Counter {
        get_points_promotion_loyalty() {
            return round_pr(this.env.pos.get_order().get_points_promotion_loyalty(), this.env.pos.loyalty.rounding);
        }
    }

    Registries.Component.add(PointsCounter);

    return PointsCounter;

});
