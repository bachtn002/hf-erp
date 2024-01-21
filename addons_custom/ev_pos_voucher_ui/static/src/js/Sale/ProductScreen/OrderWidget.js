odoo.define('ev_pos_voucher_ui.OrderWidgetVoucher', function (require) {
    'use strict';

    const OrderWidget = require('point_of_sale.OrderWidget');
    const {useListener} = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const NumberBuffer = require('point_of_sale.NumberBuffer');


    let OrderWidgetVoucher = ProductScreen =>
        class extends OrderWidget {
            constructor() {
                super(...arguments);
                useListener('edit-pack-lot-lines', this._editPackLotLines);
            }

            async _editPackLotLines(event) {
                NumberBuffer.reset();
                const order = this.env.pos.get_order();
                const orderline = event.detail.orderline;
                const isAllowOnlyOneLot = orderline.product.isAllowOnlyOneLot();
                const packLotLinesToEdit = orderline.getPackLotLinesToEdit(isAllowOnlyOneLot);
                const {confirmed, payload} = await this.showPopup('EditListPopup', {
                    title: this.env._t('Vui lòng nhập mã phiếu mua hàng để bán!'),
                    isSingleItem: isAllowOnlyOneLot,
                    array: packLotLinesToEdit,
                    product: orderline.product,
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

                    orderline.setPackLotLines({modifiedPackLotLines, newPackLotLines});
                }
                this.order.select_orderline(event.detail.orderline);
            }

        }
    Registries.Component.extend(OrderWidget, OrderWidgetVoucher);

    return OrderWidget;
});
