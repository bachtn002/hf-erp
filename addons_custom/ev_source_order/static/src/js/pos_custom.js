odoo.define('ev_source_order.models', function (require) {
    "use strict"

    const models = require('point_of_sale.models');

    models.load_models([
        {
            model:  'source.order',
            fields: ['name'],
            loaded: function(self,sources){
                self.sources = sources;
                self.source_by_id = {};
                for (var i = 0; i < sources.length; i++){
                    self.source_by_id[sources[i].id] = sources[i];
                }
            },
        },
    ]);

    var OrderSupper = models.Order;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            this.x_source_order_id = options.x_source_order_id || '';
            OrderSupper.prototype.initialize.apply(this, arguments);
            return this;
        },
        init_from_JSON: function (json) {
            this.x_source_order_id = json.x_source_order_id;
            OrderSupper.prototype.init_from_JSON.call(this, json);
        },
        export_as_JSON: function () {
            var data = OrderSupper.prototype.export_as_JSON.apply(this, arguments);
            data.x_source_order_id = this.get_x_source_order_id();
            return data;
        },
        export_for_printing: function () {
            let res = OrderSupper.prototype.export_for_printing.apply(this, arguments);
            res.x_source_order_id = this.get_x_source_order_id();
            return res;
        },
        set_x_source_order_id: function (x_source_order_id) {
            this.x_source_order_id = x_source_order_id;
        },
        get_x_source_order_id: function () {
            return this.x_source_order_id;
        },
    });

});
