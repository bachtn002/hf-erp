odoo.define('ev_pos_voucher_ui.ButtonVoucher', function (require) {
    "use strict"

    const PosComponent = require('point_of_sale.PosComponent');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const {useListener} = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');


    class ButtonVoucher extends PosComponent {
        constructor() {
            super(...arguments);
        }

        get currentOrder() {
            return this.env.pos.get_order();
        }

        async onClickButtonVoucher(event) {
            if (!this.currentOrder) {
                this.env.pos.add_new_order();
            }
            const order = this.currentOrder;
            const orderlines = this.currentOrder.orderlines;
            let price_extra = 0.0;
            let draftPackLotLines, weight, description;
            let lot_names = []
            if (orderlines) {
                orderlines.forEach((line) => {
                    if (line.pack_lot_lines) {
                        let line_lot_name = line.pack_lot_lines.models[0].changed.lot_name;
                        if (!lot_names.includes(line_lot_name)) {
                            lot_names.push(line_lot_name);
                        }
                    }
                });
            }
            // console.log('order', order)
            const {confirmed, payload, check_product} = await this.showPopup('VoucherPopup', {
                title: this.env._t('Vui lòng nhập mã phiếu mua hàng để bán!'),
                order: order,
            });
            if (confirmed) {
                // Segregate the old and new packlot lines
                const modifiedPackLotLines = Object.fromEntries(
                    payload.newArray.filter(item => item.id).map(item => [item.id, item.text])
                );
                const newPackLotLines = payload.newArray
                    .filter(item => !item.id)
                    .map(item => ({lot_name: item.text}));
                draftPackLotLines = {modifiedPackLotLines, newPackLotLines};
            } else {
                // We don't proceed on adding product.
                return;
            }
            var product = this.env.pos.db.get_product_by_id(check_product);
            var check_merge = true;
            if (draftPackLotLines) {
                if (!lot_names.includes(draftPackLotLines.newPackLotLines[0].lot_name)) {
                    check_merge = false;
                }
            }
            // Add the product after having the extra information.
            this.currentOrder.add_product(product, {
                draftPackLotLines,
                description: description,
                price_extra: price_extra,
                quantity: weight,
                merge: check_merge,
            });
            NumberBuffer.reset();
        }
    }

    ButtonVoucher.template = 'ButtonVoucher';
    // ProductScreen.addControlButton({
    //     component: ButtonVoucher,
    //     condition: function () {
    //         return true;
    //     },
    // });
    Registries.Component.add(ButtonVoucher);

    return ButtonVoucher

});

