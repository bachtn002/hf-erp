odoo.define("ev_pos_receipt.Order", function (require) {
    "use strict";

    var models = require("point_of_sale.models");

    var OrderSupper = models.Order;
    models.Order = models.Order.extend({
        export_for_printing: function () {
            var json = OrderSupper.prototype.export_for_printing.apply(this, arguments);
            if (this.pos.loyalty && this.get_client()) {
                json.loyalty = {
                    name: this.pos.loyalty.name,
                    client: this.get_client(),
                    points_won: this.get_won_points(),
                    points_spent: this.get_spent_points(),
                    points_total: this.get_new_total_points(),
                };
            }
            return json;
        },
    })
});
