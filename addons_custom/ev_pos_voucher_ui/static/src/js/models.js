odoo.define('ev_pos_voucher_ui.models', function (require) {
    "use strict"

    const models = require('point_of_sale.models');

    let product_fields = ['x_is_voucher'];
    models.load_fields("product.product", product_fields);

    models.load_fields('pos.payment.method',
        ['x_is_voucher']
    );

    models.load_fields('pos.payment',
        ['x_lot_id']
    );

    var _paylineproto = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        init_from_JSON: function (json) {
            _paylineproto.init_from_JSON.apply(this, arguments);
            if (json.lot_name) {
                this.lot_name = json.lot_name;
            }
        },
        export_as_JSON: function () {
            var json = _paylineproto.export_as_JSON.apply(this, arguments);
            if (this.lot_name) {
                json.lot_name = this.lot_name;
            }
            return json;
        },
    });
    var _super_orderline = models.Orderline.prototype;
    let Orderline = models.Orderline;
    models.Orderline = models.Orderline.extend({
        init_from_JSON: function (json) {
            _super_orderline.init_from_JSON.apply(this, arguments);
            this.x_is_voucher = json.x_is_voucher;
        },
        export_for_printing: function () {
            var vals = _super_orderline.export_for_printing.apply(this);
            var product = this.get_product();
            vals.x_is_voucher = product.x_is_voucher;
            return vals
        },
        export_as_JSON: function () {
            var lines = _super_orderline.export_as_JSON.apply(this);
            lines.x_is_voucher = this.x_is_voucher;
            return lines;
        },
        getPackLotLinesToEdit: function (isAllowOnlyOneLot) {
            const currentPackLotLines = this.pack_lot_lines.models;
            let nExtraLines = Math.abs(this.quantity) - currentPackLotLines.length;
            nExtraLines = nExtraLines > 0 ? nExtraLines : 1;
            if (currentPackLotLines) {
                var tempLines = currentPackLotLines
                    .map(lotLine => ({
                        id: lotLine.cid,
                        text: lotLine.get('lot_name'),
                    }))
            } else {
                var tempLines = currentPackLotLines
                    .concat(
                        Array.from(Array(nExtraLines)).map(_ => ({
                            text: '',
                        }))
                    );
            }
            return isAllowOnlyOneLot ? [tempLines[0]] : tempLines;
        },
    });
    return models;

});
